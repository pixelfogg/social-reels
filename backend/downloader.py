import os
import re
import uuid
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import yt_dlp

from backend.config import DOWNLOADS_DIR, TEMP_DIR, FFMPEG_PATH

logger = logging.getLogger(__name__)

class VideoDownloader:
    def __init__(self, output_dir: Path = DOWNLOADS_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_info(self, url: str) -> Dict[str, Any]:
        """Extract metadata from YouTube URL without downloading."""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "id": info.get("id"),
                "title": info.get("title", "Unknown Title"),
                "duration": info.get("duration", 0),
                "author": info.get("uploader", "Unknown Creator"),
                "thumbnail": info.get("thumbnail"),
                "description": info.get("description", "")[:300],
                "view_count": info.get("view_count", 0),
                "url": url,
            }

    def download(self, url: str, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> Dict[str, Any]:
        """Download YouTube video in best compatible MP4 format (up to 1080p)."""
        video_id = str(uuid.uuid4())[:8]
        out_template = str(self.output_dir / f"{video_id}_%(title).50s.%(ext)s")

        def hook(d):
            if progress_callback:
                if d.get('status') == 'downloading':
                    total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 1
                    downloaded = d.get('downloaded_bytes', 0)
                    percent = min(100.0, max(0.0, (downloaded / total_bytes) * 100))
                    speed = d.get('speed', 0)
                    eta = d.get('eta', 0)
                    progress_callback({
                        "status": "downloading",
                        "percent": round(percent, 1),
                        "speed": speed,
                        "eta": eta,
                        "downloaded_bytes": downloaded,
                        "total_bytes": total_bytes
                    })
                elif d.get('status') == 'finished':
                    progress_callback({
                        "status": "processing",
                        "percent": 100.0,
                        "message": "Finalizing download and merging streams..."
                    })

        ffmpeg_dir = str(Path(FFMPEG_PATH).parent)
        ydl_opts = {
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[ext=mp4]/best',
            'outtmpl': out_template,
            'merge_output_format': 'mp4',
            'ffmpeg_location': ffmpeg_dir,
            'progress_hooks': [hook],
            'quiet': True,
            'no_warnings': True,
            'windowsfilenames': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Find the downloaded file
            target_path = ydl.prepare_filename(info)
            target_path_mp4 = str(Path(target_path).with_suffix('.mp4'))
            
            final_path = target_path_mp4 if os.path.exists(target_path_mp4) else target_path
            
            return {
                "id": info.get("id"),
                "video_id": video_id,
                "title": info.get("title", "Untitled Video"),
                "duration": info.get("duration", 0),
                "author": info.get("uploader", "Unknown Creator"),
                "thumbnail": info.get("thumbnail"),
                "filepath": final_path,
                "url": url,
            }
