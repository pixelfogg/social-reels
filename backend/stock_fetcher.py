import os
import random
import logging
import urllib.request
from pathlib import Path
from typing import List, Optional
from backend.config import TEMP_DIR, FFMPEG_PATH

logger = logging.getLogger("videogen.stock_fetcher")

STOCK_CACHE_DIR = TEMP_DIR / "stock_assets"
STOCK_CACHE_DIR.mkdir(parents=True, exist_ok=True)

class StockFetcher:
    def __init__(self):
        pass

    def create_motion_graphic_clip(self, duration: float, theme_color: str, output_path: str) -> str:
        """Create a procedural 1080x1920 animated background clip with subtle lighting and motion."""
        import subprocess

        color_palettes = [
            ("#0f172a", "#1e1b4b"),  # Deep Navy / Indigo
            ("#18181b", "#3f3f46"),  # Dark Graphite
            ("#1e293b", "#0f766e"),  # Slate / Dark Teal
            ("#2e1065", "#4c1d95"),  # Midnight Purple
        ]
        c1, c2 = random.choice(color_palettes)
        
        # FFmpeg procedural gradient generator
        cmd = [
            FFMPEG_PATH, "-y",
            "-f", "lavfi",
            "-i", f"color=c={c1}:s=1080x1920:d={duration}",
            "-vf", f"noise=alls=10:allf=t+u,hue=s=0.5,drawgrid=w=108:h=192:t=1:c=white@0.04",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            output_path
        ]
        
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return output_path

    def get_broll_clip(self, keyword: str, duration: float, output_path: str) -> str:
        """Provide a contextual B-roll video clip or high-motion background."""
        return self.create_motion_graphic_clip(duration, theme_color="#6366f1", output_path=output_path)
