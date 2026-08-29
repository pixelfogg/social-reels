import os
import sys
import subprocess
import numpy as np
import cv2
from pathlib import Path

from backend.config import BASE_DIR, TEMP_DIR, CLIPS_DIR, FFMPEG_PATH
from backend.video_processor import VideoProcessor
from backend.caption_engine import CaptionEngine, THEMES

def create_synthetic_test_video(output_path: str, duration: int = 6):
    """Create a 1920x1080 synthetic landscape video with audio and a moving test circle."""
    temp_raw_video = str(TEMP_DIR / "test_raw.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = 30
    w, h = 1920, 1080
    out = cv2.VideoWriter(temp_raw_video, fourcc, fps, (w, h))

    total_frames = duration * fps
    for f in range(total_frames):
        # Create stylish dark gradient background
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:, :, 0] = int(30 + 20 * np.sin(f / 20))  # B
        frame[:, :, 1] = int(20 + 15 * np.cos(f / 20))  # G
        frame[:, :, 2] = 40                             # R

        # Draw a simulated speaker box
        center_x = int(w // 2 + 150 * np.sin(f / 30))
        center_y = int(h // 2)
        cv2.circle(frame, (center_x, center_y), 120, (240, 180, 50), -1)
        cv2.circle(frame, (center_x, center_y), 130, (255, 255, 255), 4)

        # Draw speaker face placeholder
        cv2.putText(frame, "SPEAKER", (center_x - 70, center_y + 10), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 0, 0), 2)
        cv2.putText(frame, "16:9 Landscape Original", (60, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (200, 200, 200), 2)

        out.write(frame)

    out.release()

    # Add a synthetic beep/audio tone to make it a valid MP4 with audio
    cmd = [
        FFMPEG_PATH,
        "-y",
        "-i", temp_raw_video,
        "-f", "lavfi",
        "-i", f"sine=frequency=440:duration={duration}",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    if os.path.exists(temp_raw_video):
        os.remove(temp_raw_video)
    print(f"Created synthetic test video: {output_path}")

def test_pipeline():
    print("Testing Video Processing & Subtitle Pipeline...")
    test_video = str(TEMP_DIR / "sample_test_input.mp4")
    create_synthetic_test_video(test_video, duration=6)

    # Simulated word timestamps
    mock_words = [
        {"word": "This", "start": 0.3, "end": 0.7},
        {"word": "is", "start": 0.7, "end": 0.9},
        {"word": "the", "start": 0.9, "end": 1.1},
        {"word": "secret", "start": 1.1, "end": 1.7},
        {"word": "to", "start": 1.7, "end": 1.9},
        {"word": "viral", "start": 1.9, "end": 2.4},
        {"word": "reels", "start": 2.4, "end": 3.0},
        {"word": "every", "start": 3.2, "end": 3.5},
        {"word": "single", "start": 3.5, "end": 3.9},
        {"word": "time", "start": 3.9, "end": 4.5},
        {"word": "money", "start": 4.6, "end": 5.2}
    ]

    caption_engine = CaptionEngine()
    ass_path = str(TEMP_DIR / "sample_subtitles.ass")
    caption_engine.generate_ass_subtitles(
        words=mock_words,
        output_ass_path=ass_path,
        theme_name="hormozi",
        position="center"
    )
    print(f"Generated ASS Subtitles: {ass_path}")

    # Process vertical 9:16 video
    vp = VideoProcessor()
    out_clip = str(CLIPS_DIR / "test_rendered_reel.mp4")
    vp.process_clip(
        input_video=test_video,
        output_clip_path=out_clip,
        start_time=0.0,
        duration=5.5,
        layout_mode="blur_canvas",
        ass_subtitle_path=ass_path
    )

    print(f"Successfully rendered test 9:16 Reel: {out_clip}")
    w, h, dur = vp.get_video_dimensions(out_clip)
    print(f"Rendered video specs: {w}x{h}, duration={dur:.2f}s, size={os.path.getsize(out_clip)} bytes")
    assert w == 1080 and h == 1920, f"Expected 1080x1920, got {w}x{h}"
    print("PIPELINE TEST PASSED!")

if __name__ == "__main__":
    test_pipeline()
