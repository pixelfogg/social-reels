import os
import cv2
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import numpy as np

from backend.config import FFMPEG_PATH, FFPROBE_PATH, TARGET_WIDTH, TARGET_HEIGHT, TEMP_DIR

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        # Load OpenCV face detector
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def get_video_dimensions(self, video_path: str) -> Tuple[int, int, float]:
        """Return (width, height, duration) using ffprobe or cv2."""
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = frame_count / fps if fps > 0 else 0
            cap.release()
            return w, h, duration
        return 1920, 1080, 0

    def analyze_speaker_tracking(self, video_path: str, start_time: float, duration: float) -> float:
        """Sample video frames to determine speaker's average center X position (0.0 to 1.0)."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return 0.5

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        start_frame = int(start_time * fps)
        total_frames = int(duration * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Sample every 15th frame (2 times per second)
        step = max(1, int(fps // 2))
        centers = []
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920

        for f_idx in range(0, total_frames, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame + f_idx)
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=4, minSize=(60, 60))
            
            if len(faces) > 0:
                # Largest face by area
                faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
                fx, fy, fw, fh = faces[0]
                face_center_x = (fx + fw / 2.0) / width
                centers.append(face_center_x)

        cap.release()

        if centers:
            # Return median center to avoid outliers
            return float(np.median(centers))
        return 0.5  # default dead center

    def build_layout_filter(
        self,
        layout_mode: str,
        orig_w: int,
        orig_h: int,
        speaker_center_x: float = 0.5
    ) -> str:
        """Construct FFmpeg filter graph string for 9:16 vertical formatting."""
        target_w = TARGET_WIDTH
        target_h = TARGET_HEIGHT

        if layout_mode == "blur_canvas":
            # 16:9 foreground centered on blurred 9:16 background
            fg_w = target_w
            fg_h = int(orig_h * (target_w / orig_w))
            # Ensure even dimensions
            fg_h = fg_h if fg_h % 2 == 0 else fg_h - 1
            fg_y = (target_h - fg_h) // 2

            # Background: scale to cover 1080x1920, crop to 1080x1920, blur, darken slightly
            # Foreground: scale to 1080x(fg_h), add subtle shadow/border, overlay in center
            filter_str = (
                f"[0:v]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
                f"crop={target_w}:{target_h},"
                f"boxblur=luma_radius=min(h\\,w)/10:luma_power=3:chroma_radius=min(h\\,w)/10,"
                f"eq=brightness=-0.12:contrast=1.05[bg];"
                f"[0:v]scale={fg_w}:{fg_h}:flags=lanczos[fg];"
                f"[bg][fg]overlay=0:{fg_y}[v]"
            )
            return filter_str

        elif layout_mode == "smart_crop" or layout_mode == "face_crop":
            # Crop 9:16 window centered on detected speaker
            desired_crop_w = int(orig_h * (9 / 16))
            max_x = orig_w - desired_crop_w

            if max_x <= 0:
                # Video is already vertical or narrower
                return f"[0:v]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h}[v]"

            center_x_px = speaker_center_x * orig_w
            crop_x = int(center_x_px - (desired_crop_w / 2))
            crop_x = max(0, min(crop_x, max_x))
            # Ensure even
            crop_x = crop_x if crop_x % 2 == 0 else crop_x - 1

            filter_str = (
                f"[0:v]crop={desired_crop_w}:{orig_h}:{crop_x}:0,"
                f"scale={target_w}:{target_h}:flags=lanczos[v]"
            )
            return filter_str

        elif layout_mode == "split_screen":
            # Stacked split screen (top half + bottom half with blur background)
            half_h = target_h // 2
            fg_w = target_w
            fg_h = int(orig_h * (target_w / orig_w))
            fg_h = fg_h if fg_h % 2 == 0 else fg_h - 1
            
            filter_str = (
                f"[0:v]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
                f"crop={target_w}:{target_h},"
                f"boxblur=20:5,eq=brightness=-0.2[bg];"
                f"[0:v]scale={fg_w}:{fg_h}[main];"
                f"[bg][main]overlay=0:{(half_h - fg_h)//2}[top_stack];"
                f"[0:v]scale={target_w}:{half_h}:force_original_aspect_ratio=increase,crop={target_w}:{half_h}[bottom_cam];"
                f"[top_stack][bottom_cam]overlay=0:{half_h}[v]"
            )
            return filter_str

        else:
            # Default: center crop
            desired_crop_w = int(orig_h * (9 / 16))
            crop_x = max(0, (orig_w - desired_crop_w) // 2)
            return f"[0:v]crop={desired_crop_w}:{orig_h}:{crop_x}:0,scale={target_w}:{target_h}:flags=lanczos[v]"

    def process_clip(
        self,
        input_video: str,
        output_clip_path: str,
        start_time: float,
        duration: float,
        layout_mode: str = "blur_canvas",
        ass_subtitle_path: Optional[str] = None
    ) -> str:
        """Cut video segment, convert to 9:16 vertical layout, and optionally burn subtitles in one fast pass."""
        orig_w, orig_h, _ = self.get_video_dimensions(input_video)
        
        # Detect speaker position if smart crop is requested
        speaker_center = 0.5
        if layout_mode in ["smart_crop", "face_crop"]:
            speaker_center = self.analyze_speaker_tracking(input_video, start_time, duration)

        layout_filter = self.build_layout_filter(layout_mode, orig_w, orig_h, speaker_center)

        # Handle subtitle overlay filter
        if ass_subtitle_path and os.path.exists(ass_subtitle_path):
            # Escape path for FFmpeg subtitles filter
            # In Windows FFmpeg, colon and backslashes in subtitle filename must be escaped
            safe_ass = str(ass_subtitle_path).replace("\\", "/").replace(":", "\\:")
            # Chain the subtitle filter onto the video output stream [v]
            filter_complex = f"{layout_filter};[v]ass='{safe_ass}'[outv]"
            map_v = "[outv]"
        else:
            filter_complex = layout_filter
            map_v = "[v]"

        cmd = [
            FFMPEG_PATH,
            "-y",
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", input_video,
            "-filter_complex", filter_complex,
            "-map", map_v,
            "-map", "0:a?",
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

        logger.info(f"Rendering Reel: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg render error: {result.stderr}")
            # If complex filter with ASS fails (e.g. font missing), try fallback without ASS filter or try subtitles filter
            if ass_subtitle_path:
                logger.warning("Retrying render with subtitles filter fallback...")
                safe_ass = str(ass_subtitle_path).replace("\\", "/").replace(":", "\\:")
                filter_complex_fallback = f"{layout_filter};[v]subtitles='{safe_ass}'[outv]"
                cmd[cmd.index("-filter_complex") + 1] = filter_complex_fallback
                fallback_res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if fallback_res.returncode == 0:
                    return output_clip_path

            raise RuntimeError(f"FFmpeg rendering failed: {result.stderr}")

        return output_clip_path
