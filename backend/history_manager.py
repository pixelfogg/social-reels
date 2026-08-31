import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.config import STORAGE_DIR

logger = logging.getLogger("videogen.history")
HISTORY_FILE = STORAGE_DIR / "history.json"

class HistoryManager:
    def __init__(self, history_file: Path = HISTORY_FILE):
        self.history_file = history_file
        self._ensure_file()

    def _ensure_file(self):
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.history_file.exists():
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump({"jobs": []}, f, indent=2, ensure_ascii=False)

    def _read_data(self) -> Dict[str, Any]:
        try:
            if self.history_file.exists():
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error reading history file: {e}")
        return {"jobs": []}

    def _write_data(self, data: Dict[str, Any]):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error writing history file: {e}")

    def save_job(
        self,
        job_id: str,
        video_meta: Dict[str, Any],
        reels: List[Dict[str, Any]],
        mode: str = "transformative_hindi",
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Save or update a processed video project in history."""
        data = self._read_data()
        jobs = data.get("jobs", [])

        # Format history record
        record = {
            "job_id": job_id,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": time.time(),
            "video_meta": {
                "title": video_meta.get("title", "Untitled Video"),
                "duration": video_meta.get("duration", 0),
                "author": video_meta.get("author", "Unknown Creator"),
                "thumbnail": video_meta.get("thumbnail"),
                "url": video_meta.get("url"),
                "video_id": video_meta.get("video_id") or video_meta.get("id")
            },
            "mode": mode,
            "config": config or {},
            "reels_count": len(reels),
            "reels": reels
        }

        # Check if already exists; if so, replace it
        existing_idx = next((i for i, j in enumerate(jobs) if j.get("job_id") == job_id), None)
        if existing_idx is not None:
            jobs[existing_idx] = record
        else:
            jobs.insert(0, record)  # Newest first

        data["jobs"] = jobs
        self._write_data(data)
        logger.info(f"Saved job {job_id} to history ({len(reels)} reels)")
        return record

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Return all jobs sorted by newest first."""
        data = self._read_data()
        jobs = data.get("jobs", [])
        # Return summary list
        summaries = []
        for j in jobs:
            summaries.append({
                "job_id": j.get("job_id"),
                "created_at": j.get("created_at"),
                "timestamp": j.get("timestamp"),
                "title": j.get("video_meta", {}).get("title", "Untitled"),
                "thumbnail": j.get("video_meta", {}).get("thumbnail"),
                "duration": j.get("video_meta", {}).get("duration", 0),
                "author": j.get("video_meta", {}).get("author", ""),
                "mode": j.get("mode", ""),
                "reels_count": j.get("reels_count", len(j.get("reels", []))),
                "first_reel_preview": j.get("reels", [{}])[0].get("video_url") if j.get("reels") else None
            })
        return summaries

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Fetch full job data including all reels."""
        data = self._read_data()
        for j in data.get("jobs", []):
            if j.get("job_id") == job_id:
                return j
        return None

    def delete_job(self, job_id: str) -> bool:
        """Delete a job from history."""
        data = self._read_data()
        jobs = data.get("jobs", [])
        new_jobs = [j for j in jobs if j.get("job_id") != job_id]
        if len(new_jobs) != len(jobs):
            data["jobs"] = new_jobs
            self._write_data(data)
            logger.info(f"Deleted job {job_id} from history")
            return True
        return False
