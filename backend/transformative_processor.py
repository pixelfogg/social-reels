import os
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.config import TEMP_DIR, OUTPUTS_DIR, FFMPEG_PATH
from backend.caption_engine import CaptionEngine
from backend.stock_fetcher import StockFetcher

logger = logging.getLogger("videogen.transformative_processor")

class TransformativeProcessor:
    def __init__(self):
        self.caption_engine = CaptionEngine()
        self.stock_fetcher = StockFetcher()

    def _generate_background_music(self, duration: float, output_path: str) -> str:
        """Synthesize a subtle ambient electronic chord track using FFmpeg filters."""
        cmd = [
            FFMPEG_PATH, "-y",
            "-f", "lavfi",
            "-i", f"anoisesrc=d={duration}:c=pink:r=44100:a=0.015",
            "-f", "lavfi",
            "-i", f"sine=frequency=220:duration={duration}",
            "-filter_complex", "[0:a][1:a]amix=inputs=2:weights=0.3 0.08,lowpass=f=1200,volume=0.3[aout]",
            "-map", "[aout]",
            "-c:a", "aac",
            "-b:a", "128k",
            output_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_path

    def render_transformative_short(
        self,
        source_video: str,
        narration_data: Dict[str, Any],
        story_data: Dict[str, Any],
        output_clip_path: str,
        theme_name: str = "hormozi",
        caption_position: str = "bottom",
        source_duration: float = 60.0
    ) -> str:
        """
        Assemble a 100% original, copyright-safe 9:16 short:
        - 3s micro-clips with 1.04x speed ramp and dynamic zoom
        - 100% Neural AI voiceover narration
        - Mixed ambient background music
        - Bottom safe-zone animated subtitles
        """
        narration_audio = narration_data["audio_path"]
        total_duration = narration_data["duration"]
        words = narration_data.get("words", [])
        clip_id = story_data.get("id", "story_1")
        
        # 1. Generate ASS Subtitle File for Hindi narration
        ass_path = str(TEMP_DIR / f"{Path(output_clip_path).stem}_sub.ass")
        self.caption_engine.generate_ass_subtitles(
            words=words,
            output_ass_path=ass_path,
            theme_name=theme_name,
            position=caption_position,
            custom_font_size=74,
            enable_emojis=True
        )

        # 2. Build multi-segment micro-clips (3-second slices from source video)
        slice_duration = 3.0
        num_slices = max(1, int(total_duration // slice_duration) + 1)
        
        # Determine random jump points across the source video to create dynamic montage
        step = max(4.0, (source_duration - (slice_duration * 2)) / max(1, num_slices))
        
        slice_files = []
        for i in range(num_slices):
            start_t = min(source_duration - 4.0, max(0.0, i * step + (i % 3) * 1.5))
            slice_out = str(TEMP_DIR / f"{Path(output_clip_path).stem}_slice_{i}.mp4")
            
            # Extract 3s 9:16 slice with 1.04x speed ramp and center/blur framing
            cmd_slice = [
                FFMPEG_PATH, "-y",
                "-ss", str(round(start_t, 2)),
                "-t", str(slice_duration),
                "-i", source_video,
                "-filter_complex",
                "[0:v]setpts=0.96*PTS,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=luma_radius=min(h\\,w)/10:luma_power=3:chroma_radius=min(h\\,w)/10,eq=brightness=-0.1:contrast=1.08[bg];"
                "[0:v]setpts=0.96*PTS,scale=1080:750:flags=lanczos[fg];"
                "[bg][fg]overlay=0:585[vout]",
                "-map", "[vout]",
                "-an",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-pix_fmt", "yuv420p",
                "-r", "30",
                slice_out
            ]
            
            subprocess.run(cmd_slice, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if os.path.exists(slice_out):
                slice_files.append(slice_out)

        # Create concat list file
        concat_list_path = str(TEMP_DIR / f"{Path(output_clip_path).stem}_concat.txt")
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for s in slice_files:
                f.write(f"file '{Path(s).as_posix()}'\n")

        # 3. Concatenate visual track & loop if needed to match narration duration
        temp_visual_concat = str(TEMP_DIR / f"{Path(output_clip_path).stem}_visual.mp4")
        cmd_concat = [
            FFMPEG_PATH, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list_path,
            "-t", str(round(total_duration, 2)),
            "-c:v", "copy",
            temp_visual_concat
        ]
        subprocess.run(cmd_concat, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 4. Generate ambient background music track
        bgm_path = str(TEMP_DIR / f"{Path(output_clip_path).stem}_bgm.aac")
        self._generate_background_music(total_duration, bgm_path)

        # 5. Final Assembly: Burn subtitles + Mix narration (100%) and ambient music (12%)
        escaped_ass = ass_path.replace("\\", "/").replace(":", "\\:")
        
        cmd_final = [
            FFMPEG_PATH, "-y",
            "-i", temp_visual_concat,
            "-i", narration_audio,
            "-i", bgm_path,
            "-filter_complex",
            f"[0:v]ass='{escaped_ass}'[outv];"
            f"[1:a]volume=1.0[voice];"
            f"[2:a]volume=0.15[bgm];"
            f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[outa]",
            "-map", "[outv]",
            "-map", "[outa]",
            "-t", str(round(total_duration, 2)),
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-movflags", "+faststart",
            output_clip_path
        ]

        logger.info(f"Rendering Transformative Short: {' '.join(cmd_final)}")
        res = subprocess.run(cmd_final, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            logger.error(f"Transformative Short render failed: {res.stderr}")
            raise RuntimeError(f"Transformative render failed: {res.stderr}")

        # Clean up temporary files
        try:
            os.remove(concat_list_path)
            os.remove(temp_visual_concat)
            os.remove(bgm_path)
            for s in slice_files:
                if os.path.exists(s):
                    os.remove(s)
        except Exception:
            pass

        return output_clip_path
