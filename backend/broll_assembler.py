import os
import cv2
import json
import uuid
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

from backend.config import OUTPUTS_DIR, TEMP_DIR, FFMPEG_PATH, FONTS_DIR
from backend.audio_vibes import audio_vibe_engine
from backend.broll_fetcher import broll_fetcher
from backend.voice_engine import voice_engine
from backend.caption_engine import CaptionEngine

logger = logging.getLogger("broll_assembler")
logger.setLevel(logging.INFO)

caption_engine = CaptionEngine()

class BRollAssembler:
    """Stitches multiple scene B-roll video clips with neural voiceover, animated captions & SFX."""

    def assemble_broll_reel(
        self,
        job_id: str,
        scenes: List[Dict[str, Any]],
        voice_id: str = "en-US-AndrewMultilingualNeural",
        audio_vibe: str = "mystery_suspense",
        caption_theme: str = "hormozi",
        caption_position: str = "bottom",
        language_mode: str = "hindi",
        framing_mode: str = "full_screen",
        elevenlabs_api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Complete pipeline: synthesize voiceover, download/prep B-roll for each scene, align word timestamps, and render 9:16 MP4."""
        job_temp = TEMP_DIR / job_id
        job_temp.mkdir(parents=True, exist_ok=True)

        # 1. Build full narrative script from scenes with natural human speech flow
        scene_scripts = [s.get("script_hi" if language_mode == "hindi" else "script_en", "") for s in scenes]
        full_script = " ".join([s.strip() for s in scene_scripts if s.strip()])
        logger.info(f"Synthesizing voiceover ({voice_id}) for script of length {len(full_script)}...")

        has_captions = caption_theme not in ["none", "None", "", None]

        # 2. Generate Neural TTS Voiceover Audio with Studio Mastering
        tts_res = voice_engine.generate_narration(
            script_text=full_script,
            voice_id=voice_id,
            output_name=f"{job_id}_narr_master",
            rate="+0%",
            align_subtitles=has_captions,
            elevenlabs_api_key=elevenlabs_api_key
        )
        voice_audio_path = tts_res["audio_path"]
        actual_duration = tts_res.get("duration", sum(s.get("target_duration", 4.0) for s in scenes))
        aligned_words = tts_res.get("words", [])

        # 3. Generate ASS Subtitle File (Only if captions are requested)
        ass_path = None
        if has_captions and aligned_words:
            ass_path = str(job_temp / "subtitles.ass")
            caption_engine.generate_ass_subtitles(
                words=aligned_words,
                output_ass_path=ass_path,
                theme_name=caption_theme,
                position=caption_position,
                enable_emojis=True
            )

        # 4. Process and Prepare Scene B-Roll Video Clips
        scene_count = len(scenes)
        scene_duration = actual_duration / max(1, scene_count)
        processed_clips = []
        used_clip_ids = []

        for idx, scene in enumerate(scenes):
            scene_idx = idx + 1
            query = scene.get("search_query", "cinematic background")
            logger.info(f"Fetching B-roll for Scene #{scene_idx}: '{query}'...")

            # Search or use selected clip
            clip_info = scene.get("selected_clip")
            raw_clip_path = str(job_temp / f"scene_{scene_idx}_raw.mp4")
            vurl = clip_info.get("video_url") if (clip_info and isinstance(clip_info, dict)) else None
            
            chosen_id = broll_fetcher.download_clip(
                video_url=vurl,
                output_path=raw_clip_path,
                duration=scene_duration + 1.0,
                query=query,
                exclude_ids=used_clip_ids
            )
            if chosen_id:
                used_clip_ids.append(chosen_id)

            # Crop & Scale to 9:16 (1080x1920) with target duration and selected framing mode
            trimmed_scene_path = str(job_temp / f"scene_{scene_idx}_916.mp4")
            self._crop_and_fit_916(raw_clip_path, trimmed_scene_path, duration=scene_duration, framing_mode=framing_mode)
            if Path(trimmed_scene_path).exists():
                processed_clips.append(trimmed_scene_path)

        if not processed_clips:
            raise RuntimeError("Failed to process any scene video clips")

        # 5. Concat visual clips together via FFmpeg Concat Protocol
        concat_list_file = job_temp / "concat_list.txt"
        with open(concat_list_file, "w") as f:
            for p in processed_clips:
                f.write(f"file '{p}'\n")

        stitched_visual_path = str(job_temp / "stitched_visual.mp4")
        concat_cmd = [
            FFMPEG_PATH, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_file),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-an",
            stitched_visual_path
        ]
        subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # 6. Generate Light Background Music (Audio Vibe)
        bgm_path = str(job_temp / "bgm.aac")
        audio_vibe_engine.generate_background_track(vibe_id=audio_vibe, duration=actual_duration, output_path=bgm_path)

        # 7. Final Master Render (Stitched 9:16 Visuals + Neural Voice + Ducked Light BGM)
        output_filename = f"{job_id}_viral_reel.mp4"
        final_output_path = str(OUTPUTS_DIR / output_filename)

        vibe_config = audio_vibe_engine.get_vibe(audio_vibe)
        # Audible and immersive cinematic background music mix (0.18 to 0.22)
        base_bgm_vol = vibe_config.get("bgm_volume", 0.18) if audio_vibe != "original_authentic" else 0.0
        bgm_vol = base_bgm_vol

        if has_captions and ass_path and os.path.exists(ass_path):
            escaped_ass = ass_path.replace(":", "\\:").replace("'", "\\'")
            video_filter = f"[0:v]ass='{escaped_ass}'[outv]"
        else:
            video_filter = "[0:v]scale=1080:1920,setsar=1[outv]"

        logger.info(f"Rendering Final Master Reel (captions={'ON' if has_captions else 'OFF'}, BGM vol={bgm_vol}) -> {final_output_path}")

        render_cmd = [
            FFMPEG_PATH, "-y",
            "-i", stitched_visual_path,
            "-i", voice_audio_path,
            "-i", bgm_path,
            "-filter_complex",
            f"{video_filter};[1:a]volume=1.0[voice];[2:a]volume={bgm_vol}[bgm];[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[outa]",
            "-map", "[outv]",
            "-map", "[outa]",
            "-t", str(actual_duration),
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            final_output_path
        ]

        res = subprocess.run(render_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            logger.warning(f"Master render filter failed, falling back to simple video/audio muxing: {res.stderr.decode('utf-8', errors='ignore')}")
            fallback_cmd = [
                FFMPEG_PATH, "-y",
                "-i", stitched_visual_path,
                "-i", voice_audio_path,
                "-i", bgm_path,
                "-filter_complex",
                f"[0:v]scale=1080:1920[outv];[1:a]volume=1.0[voice];[2:a]volume={bgm_vol}[bgm];[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[outa]",
                "-map", "[outv]",
                "-map", "[outa]",
                "-t", str(actual_duration),
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "20",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                final_output_path
            ]
            subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        return {
            "output_filename": output_filename,
            "output_path": final_output_path,
            "video_url": f"/api/video/{output_filename}",
            "download_url": f"/api/download/{output_filename}",
            "duration": actual_duration,
            "scenes_used": len(processed_clips)
        }

    def _crop_and_fit_916(
        self,
        input_video: str,
        output_video: str,
        duration: float = 4.0,
        framing_mode: str = "full_screen"
    ):
        """Scales and formats video clip to exact 1080x1920 (9:16) full-screen portrait format without black gaps."""
        target_w, target_h = 1080, 1920

        # Determine original dimensions
        cap = cv2.VideoCapture(input_video)
        orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1080
        orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1920
        cap.release()

        # If video is vertical (9:16 portrait) or full_screen is requested:
        # Scale directly to 1080x1920 edge-to-edge full screen with seamless infinite looping so it never runs out of frames
        if orig_h >= orig_w or framing_mode in ["full_screen", "full_crop", "portrait_fill"]:
            cmd = [
                FFMPEG_PATH, "-y",
                "-stream_loop", "-1",
                "-i", input_video,
                "-vf", f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h},setsar=1,fps=30",
                "-t", str(duration),
                "-an",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-pix_fmt", "yuv420p",
                output_video
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return

        # Optional: Landscape video with explicit blur_canvas requested
        fg_w = target_w
        fg_h = int(orig_h * (target_w / orig_w))
        fg_h = fg_h if fg_h % 2 == 0 else fg_h - 1
        fg_y = (target_h - fg_h) // 2

        filter_complex = (
            f"[0:v]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h},"
            f"boxblur=25:10,eq=brightness=-0.15:contrast=1.1[bg];"
            f"[0:v]scale={fg_w}:{fg_h}:flags=lanczos[fg];"
            f"[bg][fg]overlay=0:{fg_y},setsar=1,fps=30[outv]"
        )

        cmd = [
            FFMPEG_PATH, "-y",
            "-stream_loop", "-1",
            "-i", input_video,
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-t", str(duration),
            "-an",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            output_video
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

broll_assembler = BRollAssembler()
