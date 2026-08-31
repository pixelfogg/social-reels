import os
import re
import json
import uuid
import logging
import urllib.parse
import subprocess
import shutil
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.config import TEMP_DIR, FFMPEG_PATH, PEXELS_API_KEY

logger = logging.getLogger("broll_fetcher")
logger.setLevel(logging.INFO)

class BRollFetcher:
    """Searches and fetches high-definition portrait (9:16) video clips from Pexels API and internet video sources."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        self.pexels_api_key = PEXELS_API_KEY

    def _clean_search_query(self, query: str) -> str:
        """Distill query into high-impact visual nouns and actions for Pexels Video search."""
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', query).lower()
        noise_words = {
            "4k", "hd", "slow", "motion", "cinematic", "dramatic", "detail", "footage",
            "vintage", "background", "macro", "glowing", "abstract", "view", "ambient",
            "shot", "video", "clip", "render", "3d", "real", "life", "super"
        }
        words = [w for w in cleaned.split() if w and w not in noise_words and len(w) > 1]
        if not words:
            return "cinematic portrait background"
        # Return top 2-3 most distinct visual keywords
        return " ".join(words[:3])

    def search_pexels_portrait(self, query: str, count: int = 4, exclude_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Query official Pexels Video API for native portrait 9:16 video clips with deduplication."""
        if not self.pexels_api_key:
            return []

        cleaned_query = self._clean_search_query(query)
        headers = {"Authorization": self.pexels_api_key}
        params = {
            "query": cleaned_query,
            "orientation": "portrait",
            "per_page": max(count * 2, 8),
            "size": "medium"
        }

        try:
            url = "https://api.pexels.com/videos/search"
            res = self.session.get(url, headers=headers, params=params, timeout=8)
            if res.status_code != 200:
                logger.warning(f"Pexels search status {res.status_code}: {res.text[:100]}")
                params.pop("orientation", None)
                res = self.session.get(url, headers=headers, params=params, timeout=8)

            if res.status_code == 200:
                data = res.json()
                videos = data.get("videos", [])
                results = []
                excluded = set(exclude_ids or [])

                for v in videos:
                    vid_id = f"pexels_{v.get('id')}"
                    files = [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4"]
                    if not files:
                        continue

                    # Sort: prefer 1080x1920 HD, then 720x1280, then highest resolution vertical
                    def sort_key(f):
                        fw = f.get("width", 0) or 0
                        fh = f.get("height", 0) or 0
                        is_vert = fh >= fw
                        is_1080 = (fw == 1080 and fh == 1920)
                        is_720 = (fw == 720 and fh == 1280)
                        return (1 if is_1080 else 0, 1 if is_720 else 0, 1 if is_vert else 0, fw * fh)

                    files.sort(key=sort_key, reverse=True)
                    best_file = files[0]
                    video_link = best_file.get("link")
                    thumb = v.get("image") or (v.get("video_pictures", [{}])[0].get("picture") if v.get("video_pictures") else None)

                    item = {
                        "id": vid_id,
                        "source": "pexels_portrait",
                        "title": f"{cleaned_query.title()} (Pexels)",
                        "duration": v.get("duration", 5),
                        "thumbnail": thumb or "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&auto=format&fit=crop&q=60",
                        "video_url": video_link,
                        "width": best_file.get("width"),
                        "height": best_file.get("height"),
                        "query": cleaned_query,
                        "author": v.get("user", {}).get("name", "Pexels Creator"),
                        "already_used": vid_id in excluded
                    }

                    # Put un-used clips first
                    if vid_id not in excluded:
                        results.insert(0, item)
                    else:
                        results.append(item)

                if results:
                    logger.info(f"Found {len(results)} high-def Pexels portrait clips for '{cleaned_query}'")
                    return results[:count]

                # Fallback to single primary keyword if compound search has 0 results
                words = cleaned_query.split()
                if len(words) > 1:
                    logger.info(f"Retrying Pexels with single primary keyword: '{words[0]}'")
                    return self.search_pexels_portrait(words[0], count=count, exclude_ids=exclude_ids)

        except Exception as e:
            logger.warning(f"Error querying Pexels API for '{query}': {e}")

        return []

    def search_clips_for_query(self, query: str, count: int = 3) -> List[Dict[str, Any]]:
        """Search across Pexels Portrait index and internet video sources for matching footage snippets."""
        cleaned_query = re.sub(r'[^a-zA-Z0-9\s]', '', query).strip()

        # 1. First priority: Native Full-Screen Portrait Videos from Pexels API
        pexels_clips = self.search_pexels_portrait(cleaned_query, count=count)
        if pexels_clips:
            return pexels_clips

        # 2. Fallback to web search if Pexels has no clips for a specific term
        search_term = f"{cleaned_query} b roll stock footage"
        try:
            cmd = [
                "yt-dlp",
                "--default-search", f"ytsearch{count}",
                "--dump-json",
                "--flat-playlist",
                search_term
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=12)
            results = []
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().split("\n"):
                    if not line.strip():
                        continue
                    try:
                        item = json.loads(line)
                        thumb = item.get("thumbnail")
                        if not thumb and item.get("thumbnails"):
                            thumb = item["thumbnails"][-1].get("url")
                        results.append({
                            "id": item.get("id", str(uuid.uuid4())[:8]),
                            "source": "web_video",
                            "title": item.get("title", cleaned_query.title()),
                            "duration": item.get("duration", 5),
                            "thumbnail": thumb or "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&auto=format&fit=crop&q=60",
                            "video_url": f"https://www.youtube.com/watch?v={item.get('id')}" if item.get("id") else None,
                            "query": cleaned_query
                        })
                    except Exception:
                        pass

            if results:
                return results[:count]
        except Exception as e:
            logger.warning(f"Error searching web videos for '{query}': {e}")

        # Fallback preset
        fallback_results = []
        for idx in range(count):
            fallback_results.append({
                "id": f"web_clip_{idx}",
                "source": "curated_web",
                "title": f"{cleaned_query.title()} Clip #{idx+1}",
                "duration": 5,
                "thumbnail": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&auto=format&fit=crop&q=60",
                "video_url": "https://www.youtube.com/watch?v=UF8uR6Z6KLc",
                "query": cleaned_query
            })
        return fallback_results

    def download_direct_mp4(self, url: str, output_path: str) -> bool:
        """Stream direct high-speed MP4 file from Pexels or CDN to local disk."""
        try:
            logger.info(f"Streaming direct high-speed MP4 from Pexels CDN -> {output_path}...")
            with self.session.get(url, stream=True, timeout=25) as r:
                r.raise_for_status()
                with open(output_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=131072):
                        if chunk:
                            f.write(chunk)
            
            if Path(output_path).exists() and Path(output_path).stat().st_size > 50000:
                logger.info(f"Direct MP4 download completed ({Path(output_path).stat().st_size} bytes)")
                return True
        except Exception as e:
            logger.warning(f"Failed direct MP4 download from {url[:80]}: {e}")
        return False

    def download_clip(
        self,
        video_url: Optional[str],
        output_path: str,
        duration: float = 4.5,
        query: Optional[str] = None,
        exclude_ids: Optional[List[str]] = None
    ) -> Optional[str]:
        """Fetch and extract a portrait video snippet directly from Pexels or web video, returning the clip id."""
        # 1. Clean up any existing stale files at output destination
        for f in [output_path, f"{output_path}.part", f"{output_path}.webm", f"{output_path}.mp4"]:
            if Path(f).exists():
                try:
                    os.remove(f)
                except Exception:
                    pass

        # 2. If video_url is a direct Pexels/CDN MP4 link, download directly via HTTP stream
        if video_url and ("pexels.com" in video_url or video_url.endswith(".mp4") or "video-files" in video_url):
            if self.download_direct_mp4(video_url, output_path):
                return video_url

        # 3. If no direct URL provided, first search Pexels portrait index for matching query
        raw_query = query or "cinematic dramatic background"
        clean_q = re.sub(r'[^a-zA-Z0-9\s]', ' ', raw_query).strip()
        pexels_clips = self.search_pexels_portrait(clean_q, count=4, exclude_ids=exclude_ids)
        
        # Pick best unused clip
        chosen_clip = None
        if pexels_clips:
            for c in pexels_clips:
                if not c.get("already_used") and c.get("video_url"):
                    chosen_clip = c
                    break
            if not chosen_clip and pexels_clips[0].get("video_url"):
                chosen_clip = pexels_clips[0]

        if chosen_clip and chosen_clip.get("video_url"):
            if self.download_direct_mp4(chosen_clip["video_url"], output_path):
                return chosen_clip.get("id")

        # 4. Fallback to yt-dlp snippet download if Pexels has no direct file
        clean_words = [w for w in clean_q.split() if len(w) > 1]
        target_term = " ".join(clean_words[:3]) if clean_words else "cinematic dramatic b roll"

        if video_url and video_url.startswith("http") and "UF8uR6Z6KLc" not in video_url:
            search_target = video_url
        else:
            search_target = f"ytsearch1:{target_term} 4k portrait b roll"

        logger.info(f"Downloading web video snippet for '{search_target}' -> {output_path}...")

        try:
            cmd = [
                "yt-dlp",
                "--ffmpeg-location", FFMPEG_PATH,
                "--format", "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
                "--merge-output-format", "mp4",
                "--max-filesize", "30M",
                "-o", output_path,
                search_target
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            logger.info(f"yt-dlp exit {res.returncode}")
            
            if Path(output_path).exists() and Path(output_path).stat().st_size > 50000:
                logger.info(f"Successfully downloaded web clip ({Path(output_path).stat().st_size} bytes)")
                return True

            for alt in [f"{output_path}.mp4", f"{output_path}.webm", f"{output_path}.mkv"]:
                if Path(alt).exists() and Path(alt).stat().st_size > 50000:
                    shutil.move(alt, output_path)
                    logger.info(f"Successfully moved clip from {alt}")
                    return True

        except Exception as e:
            logger.warning(f"Failed to fetch video snippet: {e}")

        # Fallback to high quality procedural generator if all networks fail
        logger.warning(f"Using procedural visual fallback for {output_path}")
        return self._generate_procedural_clip(output_path, duration=duration)

    def _generate_procedural_clip(self, output_path: str, duration: float = 5.0) -> bool:
        """Generate high quality ambient dynamic gradient video clip via FFmpeg."""
        try:
            cmd = [
                FFMPEG_PATH, "-y",
                "-f", "lavfi",
                "-i", f"testsrc2=s=1080x1920:r=30",
                "-filter_complex",
                "boxblur=25:12,eq=brightness=-0.15:contrast=1.25:saturation=1.4",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-pix_fmt", "yuv420p",
                "-t", str(duration),
                output_path
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return res.returncode == 0 and Path(output_path).exists() and Path(output_path).stat().st_size > 1000
        except Exception as e:
            logger.error(f"Error creating procedural clip: {e}")
            return False

broll_fetcher = BRollFetcher()

