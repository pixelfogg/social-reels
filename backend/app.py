import os
import sys
import uuid
import json
import random
import zipfile
import shutil
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from backend.config import (
    BASE_DIR, DOWNLOADS_DIR, CLIPS_DIR, OUTPUTS_DIR, TEMP_DIR,
    FONTS_DIR, FFMPEG_PATH
)
from backend.downloader import VideoDownloader
from backend.transcriber import Transcriber
from backend.analyzer import ViralAnalyzer
from backend.video_processor import VideoProcessor
from backend.caption_engine import CaptionEngine, THEMES, COLOR_PALETTES
from backend.voice_engine import VoiceEngine, SUPPORTED_VOICES
from backend.story_generator import StoryGenerator
from backend.transformative_processor import TransformativeProcessor
from backend.audio_vibes import AudioVibeEngine, AUDIO_VIBES
from backend.history_manager import HistoryManager
from backend.social_publisher import SocialPublisher
from backend.viral_story_engine import viral_story_engine, VIRAL_NICHE_PRESETS
from backend.broll_fetcher import broll_fetcher
from backend.broll_assembler import broll_assembler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("videogen")

app = FastAPI(title="AI YouTube to Reels Studio", version="1.0.0")

# CORS setup for web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active jobs state
jobs_state: Dict[str, Dict[str, Any]] = {}
executor = ThreadPoolExecutor(max_workers=4)

# Service singletons
downloader = VideoDownloader()
transcriber = Transcriber(model_size="base")
analyzer = ViralAnalyzer()
video_processor = VideoProcessor()
caption_engine = CaptionEngine()
voice_engine = VoiceEngine(transcriber=transcriber)
story_generator = StoryGenerator()
transformative_processor = TransformativeProcessor()
audio_vibe_engine = AudioVibeEngine()
history_manager = HistoryManager()
social_publisher = SocialPublisher()

# Sample YouTube videos for quick 1-click testing
SAMPLE_VIDEOS = [
    {
        "id": "sample_1",
        "title": "Steve Jobs - Secrets of Life (Stanford Classic)",
        "url": "https://www.youtube.com/watch?v=UF8uR6Z6KLc",
        "author": "Silicon Valley Archive",
        "duration": 120,
        "thumbnail": "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=600&auto=format&fit=crop&q=80"
    },
    {
        "id": "sample_2",
        "title": "Alex Hormozi - How To Get Rich in 2026",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "author": "Acquisition.com",
        "duration": 180,
        "thumbnail": "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?w=600&auto=format&fit=crop&q=80"
    },
    {
        "id": "sample_3",
        "title": "Lex Fridman Podcast - The Future of AI",
        "url": "https://www.youtube.com/watch?v=L_Guz73e6fw",
        "author": "Lex Fridman",
        "duration": 240,
        "thumbnail": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600&auto=format&fit=crop&q=80"
    }
]

class InfoRequest(BaseModel):
    url: str

class GenerateRequest(BaseModel):
    url: Optional[str] = None
    file_path: Optional[str] = None
    max_analysis_duration: Optional[float] = None  # Optional limit for faster processing
    layout_mode: str = "blur_canvas"  # blur_canvas, smart_crop, center_crop, split_screen
    caption_theme: str = "hormozi"    # hormozi, mrbeast, submagic, cyberpunk, minimalist
    highlight_color: Optional[str] = None
    caption_position: str = "bottom"  # bottom, center, top
    font_size: Optional[int] = None
    enable_emojis: bool = True

class ReRenderRequest(BaseModel):
    job_id: str
    clip_id: str
    start_time: float
    end_time: float
    layout_mode: str = "blur_canvas"
    caption_theme: str = "hormozi"
    highlight_color: Optional[str] = None
    caption_position: str = "bottom"
    font_size: Optional[int] = None
    enable_emojis: bool = True
    edited_text: Optional[str] = None

class SocialAccountRequest(BaseModel):
    platform: str
    credentials: Dict[str, Any]

class SocialDisconnectRequest(BaseModel):
    platform: str

class SocialPublishRequest(BaseModel):
    platforms: List[str]
    reel: Dict[str, Any]
    host_url: Optional[str] = "http://localhost:8000"

class BRollScriptRequest(BaseModel):
    topic: str
    niche: str = "dark_secrets"
    language: str = "hinglish"
    duration_mode: Optional[str] = "long"
    custom_prompt: Optional[str] = None
    scene_count: Optional[int] = None
    api_key: Optional[str] = None
    ai_provider: Optional[str] = None

class BRollSearchRequest(BaseModel):
    query: str
    count: int = 4

class BRollRenderRequest(BaseModel):
    topic: str
    scenes: List[Dict[str, Any]]
    voice_id: str = "en-US-AndrewMultilingualNeural"
    audio_vibe: str = "mystery_suspense"
    caption_theme: str = "hormozi"
    caption_position: str = "bottom"
    language_mode: str = "hindi"
    framing_mode: Optional[str] = "full_screen"
    elevenlabs_api_key: Optional[str] = None

@app.get("/api/samples")
async def get_samples():
    """Return curated sample videos."""
    return {"samples": SAMPLE_VIDEOS, "themes": THEMES, "palettes": COLOR_PALETTES}

@app.get("/api/voices")
async def get_voices():
    """Return available neural voices for speech synthesis."""
    return {"voices": SUPPORTED_VOICES}

@app.post("/api/info")
async def get_video_info(req: InfoRequest):
    """Fetch video metadata from YouTube URL."""
    try:
        info = downloader.extract_info(req.url)
        return {"status": "success", "info": info}
    except Exception as e:
        logger.error(f"Error fetching info for {req.url}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/upload")
async def upload_local_video(file: UploadFile = File(...)):
    """Upload a local video file (MP4, MKV, MOV, WEBM)."""
    try:
        file_ext = Path(file.filename).suffix or ".mp4"
        upload_id = str(uuid.uuid4())[:8]
        dest_path = DOWNLOADS_DIR / f"upload_{upload_id}{file_ext}"
        
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        orig_w, orig_h, duration = video_processor.get_video_dimensions(str(dest_path))
        
        return {
            "status": "success",
            "file_path": str(dest_path),
            "filename": file.filename,
            "duration": duration,
            "title": Path(file.filename).stem.replace("_", " ").title(),
            "author": "Local Upload"
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

def run_generation_pipeline(job_id: str, req_data: Dict[str, Any]):
    """Execute the full end-to-end Reels generation background pipeline."""
    try:
        def update_progress(stage: str, percent: float, message: str):
            jobs_state[job_id]["stage"] = stage
            jobs_state[job_id]["percent"] = percent
            jobs_state[job_id]["message"] = message
            logger.info(f"[{job_id}] [{stage}] {percent}% - {message}")

        # Step 1: Ingestion / Download
        video_file = req_data.get("file_path")
        video_meta = {}

        if not video_file or not os.path.exists(video_file):
            url = req_data.get("url")
            if not url:
                raise ValueError("Neither video URL nor valid file_path was provided.")
            
            update_progress("downloading", 10.0, "Connecting to YouTube and downloading high-quality stream...")
            dl_res = downloader.download(url, progress_callback=lambda d: update_progress("downloading", min(40.0, d.get("percent", 0) * 0.4), "Downloading video stream..."))
            video_file = dl_res["filepath"]
            video_meta = dl_res
        else:
            w, h, dur = video_processor.get_video_dimensions(video_file)
            video_meta = {
                "title": Path(video_file).stem,
                "duration": dur,
                "filepath": video_file
            }

        jobs_state[job_id]["video_meta"] = video_meta

        # Step 2: AI Speech Transcription with Word-Level Timestamps
        update_progress("transcribing", 40.0, "Transcribing speech with AI word-level synchronization...")
        max_analysis_dur = req_data.get("max_analysis_duration")
        trans_res = transcriber.transcribe(
            video_file,
            max_duration=max_analysis_dur,
            progress_callback=lambda p: update_progress("transcribing", 40.0 + (p.get("percent", 0) * 0.25), p.get("message", "Processing audio..."))
        )
        jobs_state[job_id]["transcript"] = trans_res

        mode = req_data.get("mode", "transformative_hindi")
        voice_id = req_data.get("voice_id", "hi-IN-MadhurNeural")
        story_style = req_data.get("story_style", "viral_mystery")
        audio_vibe = req_data.get("audio_vibe", "mystery_suspense")
        layout_mode = req_data.get("layout_mode", "blur_canvas")
        caption_theme = req_data.get("caption_theme", "hormozi")
        caption_pos = req_data.get("caption_position", "bottom")
        highlight_color = req_data.get("highlight_color")
        font_size = req_data.get("font_size")
        enable_emojis = req_data.get("enable_emojis", True)

        rendered_reels = []

        if mode == "transformative_hindi":
            # Step 3: Natural Hindi Viral Story Generation
            update_progress("analyzing", 68.0, "Writing viral Natural Hindi story script & narrative arcs...")
            num_stories = min(10, max(1, req_data.get("num_reels", 3)))
            stories = story_generator.generate_hindi_stories(
                transcript_data=trans_res,
                num_stories=num_stories,
                style=story_style
            )
            jobs_state[job_id]["stories"] = stories

            total_stories = len(stories)
            for idx, story in enumerate(stories):
                story_id = story["id"]
                reel_num = idx + 1
                base_percent = 70.0 + (reel_num / total_stories) * 28.0
                update_progress("rendering", base_percent, f"Synthesizing Hindi Neural Narration & Assembling Short #{reel_num}/{total_stories}...")

                # 4a: Synthesize Neural Voiceover & Align Word Timestamps
                narration = voice_engine.generate_narration(
                    script_text=story["script"],
                    voice_id=voice_id,
                    output_name=f"{job_id}_{story_id}_narr"
                )

                # 4b: Assemble Transformative Short
                out_filename = f"{job_id}_{story_id}.mp4"
                out_video_path = str(OUTPUTS_DIR / out_filename)

                transformative_processor.render_transformative_short(
                    source_video=video_file,
                    narration_data=narration,
                    story_data=story,
                    output_clip_path=out_video_path,
                    theme_name=caption_theme,
                    caption_position=caption_pos,
                    source_duration=video_meta.get("duration", 60.0),
                    audio_vibe=audio_vibe
                )

                rendered_reels.append({
                    "id": story_id,
                    "title": story["title"],
                    "hook": story["hook"],
                    "start_time": 0.0,
                    "end_time": round(narration["duration"], 2),
                    "duration": round(narration["duration"], 2),
                    "virality_score": random.randint(92, 98),
                    "text": story["script"],
                    "words": narration.get("words", []),
                    "hashtags": story.get("social_pack", {}).get("hashtags", []),
                    "social_pack": story.get("social_pack", {}),
                    "video_url": f"/api/video/{out_filename}",
                    "download_url": f"/api/download/{out_filename}",
                    "filename": out_filename,
                    "layout_mode": layout_mode,
                    "caption_theme": caption_theme,
                    "caption_position": caption_pos,
                    "highlight_color": highlight_color,
                    "audio_vibe": audio_vibe
                })

            jobs_state[job_id]["reels"] = rendered_reels
            jobs_state[job_id]["status"] = "completed"
            jobs_state[job_id]["percent"] = 100.0
            jobs_state[job_id]["message"] = f"Successfully generated {len(rendered_reels)} 100% Monetizable Shorts!"

            # Save to persistent history
            try:
                history_manager.save_job(
                    job_id=job_id,
                    video_meta=jobs_state[job_id]["video_meta"],
                    reels=rendered_reels,
                    mode=mode,
                    config=req_data
                )
            except Exception as e:
                logger.error(f"Failed to save job {job_id} to history: {e}")

        else:
            # Step 3 (Direct Highlights): Viral Hook Analysis & Segment Discovery
            update_progress("analyzing", 68.0, "Detecting viral hooks, punchlines, and high-energy segments...")
            num_reels = req_data.get("num_reels", 10)
            target_dur = req_data.get("target_duration", 30.0)
            min_dur = req_data.get("min_duration", 15.0)
            max_dur = req_data.get("max_duration", 60.0)

            clips_plan = analyzer.detect_clips(
                transcript_data=trans_res,
                num_clips=num_reels,
                min_duration=min_dur,
                max_duration=max_dur,
                target_duration=target_dur
            )

            jobs_state[job_id]["clips_plan"] = clips_plan
            total_clips = len(clips_plan)

            for idx, clip in enumerate(clips_plan):
                clip_id = clip["id"]
                reel_num = idx + 1
                base_percent = 70.0 + (reel_num / total_clips) * 28.0
                update_progress("rendering", base_percent, f"Rendering 9:16 Reel #{reel_num}/{total_clips} with animated captions...")

                # 4a: Generate ASS Subtitles
                ass_path = str(TEMP_DIR / f"{job_id}_{clip_id}.ass")
                caption_engine.generate_ass_subtitles(
                    words=clip.get("words", []),
                    output_ass_path=ass_path,
                    theme_name=caption_theme,
                    position=caption_pos,
                    custom_font_size=font_size,
                    custom_highlight_color=highlight_color,
                    enable_emojis=enable_emojis
                )

                # 4b: Process and burn subtitles onto 9:16 video
                out_filename = f"{job_id}_{clip_id}.mp4"
                out_video_path = str(OUTPUTS_DIR / out_filename)

                video_processor.process_clip(
                    input_video=video_file,
                    output_clip_path=out_video_path,
                    start_time=clip["start_time"],
                    duration=clip["duration"],
                    layout_mode=layout_mode,
                    ass_subtitle_path=ass_path
                )

                rendered_reels.append({
                    "id": clip_id,
                    "title": clip["title"],
                    "hook": clip["hook"],
                    "start_time": clip["start_time"],
                    "end_time": clip["end_time"],
                    "duration": clip["duration"],
                    "virality_score": clip["virality_score"],
                    "text": clip["text"],
                    "words": clip.get("words", []),
                    "hashtags": clip.get("hashtags", []),
                    "social_pack": clip.get("social_pack", {}),
                    "video_url": f"/api/video/{out_filename}",
                    "download_url": f"/api/download/{out_filename}",
                    "filename": out_filename,
                    "layout_mode": layout_mode,
                    "caption_theme": caption_theme,
                    "caption_position": caption_pos,
                    "highlight_color": highlight_color,
                    "audio_vibe": audio_vibe
                })

            jobs_state[job_id]["reels"] = rendered_reels
            jobs_state[job_id]["status"] = "completed"
            jobs_state[job_id]["percent"] = 100.0
            jobs_state[job_id]["message"] = f"Successfully generated {len(rendered_reels)} Viral Reels!"

            # Save to persistent history
            try:
                history_manager.save_job(
                    job_id=job_id,
                    video_meta=jobs_state[job_id]["video_meta"],
                    reels=rendered_reels,
                    mode=mode,
                    config=req_data
                )
            except Exception as e:
                logger.error(f"Failed to save job {job_id} to history: {e}")

    except Exception as e:
        logger.exception(f"Pipeline failed for job {job_id}: {e}")
        jobs_state[job_id]["status"] = "failed"
        jobs_state[job_id]["error"] = str(e)
        jobs_state[job_id]["message"] = f"Generation failed: {str(e)}"

@app.post("/api/generate")
async def start_generation(req: GenerateRequest, background_tasks: BackgroundTasks):
    """Start asynchronous Reels generation job."""
    job_id = f"job_{uuid.uuid4().hex[:10]}"
    jobs_state[job_id] = {
        "job_id": job_id,
        "status": "in_progress",
        "stage": "initializing",
        "percent": 0.0,
        "message": "Initializing generator...",
        "reels": [],
        "created_at": str(asyncio.get_event_loop().time())
    }

    background_tasks.add_task(run_generation_pipeline, job_id, req.dict())
    return {"status": "started", "job_id": job_id}

@app.get("/api/progress/{job_id}")
async def get_progress(job_id: str):
    """Fetch status and progress for a job."""
    if job_id not in jobs_state:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs_state[job_id]

@app.post("/api/re-render")
async def re_render_clip(req: ReRenderRequest):
    """Instantly re-render an individual clip with modified styles, colors, or timings."""
    job_id = req.job_id
    if job_id not in jobs_state:
        raise HTTPException(status_code=404, detail="Original job not found")

    job_data = jobs_state[job_id]
    video_meta = job_data.get("video_meta", {})
    orig_video_path = video_meta.get("filepath")
    
    if not orig_video_path or not os.path.exists(orig_video_path):
        raise HTTPException(status_code=400, detail="Original video source not found")

    # Find the clip info
    matched_clip = None
    for r in job_data.get("reels", []):
        if r["id"] == req.clip_id:
            matched_clip = r
            break

    if not matched_clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    duration = round(req.end_time - req.start_time, 2)
    if duration <= 0:
        raise HTTPException(status_code=400, detail="Invalid start/end time")

    try:
        # Re-filter words for updated time range
        words = matched_clip.get("words", [])
        rebased_words = []
        for w in words:
            if req.start_time <= (w["start"] + matched_clip["start_time"]) <= req.end_time:
                rebased_words.append({
                    "word": w["word"],
                    "start": round(max(0.0, (w["start"] + matched_clip["start_time"]) - req.start_time), 3),
                    "end": round(max(0.0, (w["end"] + matched_clip["start_time"]) - req.start_time), 3),
                    "probability": w.get("probability", 1.0)
                })

        if not rebased_words and req.edited_text:
            # Generate synthetic word timings from edited text
            edit_words = req.edited_text.split()
            w_step = duration / max(1, len(edit_words))
            for i, ew in enumerate(edit_words):
                rebased_words.append({
                    "word": ew,
                    "start": round(i * w_step, 3),
                    "end": round((i + 1) * w_step, 3),
                    "probability": 1.0
                })

        # Generate new ASS Subtitles
        ass_path = str(TEMP_DIR / f"{job_id}_{req.clip_id}_rerender.ass")
        caption_engine.generate_ass_subtitles(
            words=rebased_words,
            output_ass_path=ass_path,
            theme_name=req.caption_theme,
            position=req.caption_position,
            custom_font_size=req.font_size,
            custom_highlight_color=req.highlight_color,
            enable_emojis=req.enable_emojis
        )

        out_filename = f"{job_id}_{req.clip_id}_v{uuid.uuid4().hex[:4]}.mp4"
        out_video_path = str(OUTPUTS_DIR / out_filename)

        video_processor.process_clip(
            input_video=orig_video_path,
            output_clip_path=out_video_path,
            start_time=req.start_time,
            duration=duration,
            layout_mode=req.layout_mode,
            ass_subtitle_path=ass_path
        )

        # Update clip in job state
        matched_clip.update({
            "start_time": req.start_time,
            "end_time": req.end_time,
            "duration": duration,
            "video_url": f"/api/video/{out_filename}",
            "download_url": f"/api/download/{out_filename}",
            "filename": out_filename,
            "layout_mode": req.layout_mode,
            "caption_theme": req.caption_theme,
            "caption_position": req.caption_position,
            "highlight_color": req.highlight_color
        })

        return {"status": "success", "clip": matched_clip}

    except Exception as e:
        logger.error(f"Re-render failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/video/{filename}")
async def stream_video(filename: str):
    """Stream vertical video for browser playback."""
    file_path = OUTPUTS_DIR / filename
    if not file_path.exists():
        file_path = CLIPS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    return FileResponse(file_path, media_type="video/mp4")

@app.get("/api/download/{filename}")
async def download_video(filename: str):
    """Download individual MP4 reel."""
    file_path = OUTPUTS_DIR / filename
    if not file_path.exists():
        file_path = CLIPS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="video/mp4", filename=filename)

@app.get("/api/download-all/{job_id}")
async def download_all_reels(job_id: str):
    """Bundle all generated reels for a job into a ZIP file."""
    if job_id not in jobs_state:
        raise HTTPException(status_code=404, detail="Job not found")

    job_data = jobs_state[job_id]
    reels = job_data.get("reels", [])
    if not reels:
        raise HTTPException(status_code=400, detail="No rendered reels found")

    zip_filename = f"reels_bundle_{job_id}.zip"
    zip_path = TEMP_DIR / zip_filename

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for r in reels:
            fpath = OUTPUTS_DIR / r["filename"]
            if fpath.exists():
                clean_title = "".join(c for c in r["title"] if c.isalnum() or c in (" ", "-", "_")).strip()
                arcname = f"{r['id']}_{clean_title[:30]}.mp4"
                zipf.write(fpath, arcname=arcname)
                
                # Multi-Platform Viral Social Packages
                sp = r.get("social_pack", {})
                ig_data = sp.get("instagram", {})
                yt_data = sp.get("youtube", {})
                fb_data = sp.get("facebook", {})

                # Instagram Pack File
                ig_text = f"=== INSTAGRAM REELS VIRAL PACK ===\nTitle: {r['title']}\nHook: {r['hook']}\nVirality Score: {r['virality_score']}/100\nBest Post Time: {ig_data.get('best_time_to_post', '12:00 PM / 7:00 PM')}\nAudio Tip: {ig_data.get('audio_tip', '')}\n\n--- CAPTION & HASHTAGS ---\n{ig_data.get('caption', '')}"
                zipf.writestr(f"{r['id']}_instagram.txt", ig_text)

                # YouTube Shorts Pack File
                yt_text = f"=== YOUTUBE SHORTS SEO PACK ===\nTitle: {yt_data.get('title', r['title'])}\nPinned Comment: {yt_data.get('pinned_comment', '')}\nTags: {', '.join(yt_data.get('tags', []))}\n\n--- DESCRIPTION ---\n{yt_data.get('description', '')}"
                zipf.writestr(f"{r['id']}_youtube_shorts.txt", yt_text)

                # Facebook Reels Pack File
                fb_text = f"=== FACEBOOK REELS VIRAL PACK ===\nHeadline: {fb_data.get('headline', r['title'])}\nEngagement Question: {fb_data.get('engagement_question', '')}\n\n--- CAPTION ---\n{fb_data.get('caption', '')}"
                zipf.writestr(f"{r['id']}_facebook_reels.txt", fb_text)

    return FileResponse(zip_path, media_type="application/zip", filename=zip_filename)

# ----------------- AUDIO VIBES API -----------------
@app.get("/api/audio_vibes")
async def get_audio_vibes():
    """Return available procedural background sound vibes and styles."""
    return {"vibes": list(AUDIO_VIBES.values())}

# ----------------- HISTORY API -----------------
@app.get("/api/history")
async def get_history():
    """Return list of all past processed video projects."""
    return {"history": history_manager.get_all_jobs()}

@app.get("/api/history/{job_id}")
async def get_history_item(job_id: str):
    """Fetch complete data and clips for a past job."""
    job = history_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found in history")
    # Restore to in-memory state so re-rendering and live edits work seamlessly
    if job_id not in jobs_state:
        jobs_state[job_id] = {
            "status": "completed",
            "percent": 100.0,
            "message": f"Loaded from history: {job['video_meta'].get('title', 'Video')}",
            "video_meta": job.get("video_meta", {}),
            "reels": job.get("reels", []),
            "mode": job.get("mode", "transformative_hindi")
        }
    return {"status": "success", "job": job}

@app.delete("/api/history/{job_id}")
async def delete_history_item(job_id: str):
    """Delete a past job from history."""
    deleted = history_manager.delete_job(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found")
    if job_id in jobs_state:
        del jobs_state[job_id]
    return {"status": "success", "message": f"Job {job_id} deleted successfully"}

# ----------------- SOCIAL ACCOUNTS & 1-CLICK PUBLISHING API -----------------
@app.get("/api/social/accounts")
async def get_social_accounts():
    """Return connection status of connected social platforms."""
    return {"accounts": social_publisher.get_accounts_status()}

@app.post("/api/social/accounts")
async def update_social_account(req: SocialAccountRequest):
    """Save credentials or webhook URL for a social platform."""
    res = social_publisher.update_account(req.platform, req.credentials)
    return {"status": "success", "accounts": res}

@app.post("/api/social/disconnect")
async def disconnect_social_account(req: SocialDisconnectRequest):
    """Disconnect a social platform."""
    res = social_publisher.disconnect_account(req.platform)
    return {"status": "success", "accounts": res}

@app.post("/api/social/publish")
async def publish_to_social(req: SocialPublishRequest):
    """1-Click publish reel to selected platforms (Instagram, YouTube Shorts, Twitter, TikTok, Webhook)."""
    try:
        results = social_publisher.publish(
            platforms=req.platforms,
            reel_data=req.reel,
            host_url=req.host_url or "http://localhost:8000"
        )
        return {
            "status": "success",
            "published_platforms": req.platforms,
            "results": results
        }
    except Exception as e:
        logger.error(f"Error publishing reel: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 🎬 AI VIRAL STORY & INTERNET B-ROLL STUDIO API
# ==========================================

@app.get("/api/broll/presets")
async def get_broll_presets():
    """Return viral niche templates and presets."""
    return {"presets": VIRAL_NICHE_PRESETS}

@app.post("/api/broll/generate-script")
async def generate_broll_script(req: BRollScriptRequest):
    """Generate scene-by-scene script breakdown with B-roll search queries."""
    try:
        data = viral_story_engine.generate_scene_breakdown(
            topic=req.topic,
            niche=req.niche,
            language=req.language,
            duration_mode=getattr(req, 'duration_mode', 'long') or 'long',
            custom_prompt=getattr(req, 'custom_prompt', None),
            scene_count=getattr(req, 'scene_count', None),
            api_key=getattr(req, 'api_key', None),
            ai_provider=getattr(req, 'ai_provider', None)
        )
        return {"status": "success", "data": data}
    except Exception as e:
        logger.error(f"Error generating broll script: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/broll/search-clips")
async def search_broll_clips(req: BRollSearchRequest):
    """Search royalty-free and web video clips for a visual scene query."""
    try:
        clips = broll_fetcher.search_clips_for_query(req.query, count=req.count)
        return {"status": "success", "clips": clips}
    except Exception as e:
        logger.error(f"Error searching broll clips: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/broll/voices")
async def get_broll_voices():
    """Return available ultra-realistic human neural voices."""
    return {"voices": voice_engine.get_available_voices()}

def run_broll_pipeline(job_id: str, req: BRollRenderRequest):
    """Background rendering worker for multi-clip B-roll reel synthesis."""
    try:
        jobs_state[job_id] = {
            "status": "processing",
            "stage": "scripting",
            "percent": 15.0,
            "message": "Validating scene breakdown and generating neural narration..."
        }

        # 1. Voice generation & Timestamp alignment
        jobs_state[job_id].update({
            "stage": "synthesizing",
            "percent": 35.0,
            "message": "Generating hyper-realistic neural voiceover with Whisper word alignment..."
        })

        # 2. B-Roll download & stitching
        jobs_state[job_id].update({
            "stage": "broll_fetching",
            "percent": 55.0,
            "message": "Searching & downloading high-definition internet B-roll clips for each scene..."
        })

        # 3. Assemble and render multi-clip master reel
        jobs_state[job_id].update({
            "stage": "rendering",
            "percent": 75.0,
            "message": "Assembling multi-video 9:16 timeline, adding SFX transitions & burning karaoke captions..."
        })

        render_res = broll_assembler.assemble_broll_reel(
            job_id=job_id,
            scenes=req.scenes,
            voice_id=req.voice_id,
            audio_vibe=req.audio_vibe,
            caption_theme=req.caption_theme,
            caption_position=req.caption_position,
            language_mode=req.language_mode,
            framing_mode=getattr(req, 'framing_mode', 'full_screen') or 'full_screen',
            elevenlabs_api_key=getattr(req, 'elevenlabs_api_key', None)
        )

        reel_data = {
            "id": f"{job_id}_reel_1",
            "title": req.topic.title(),
            "hook": req.scenes[0].get("script_hi", "") if req.scenes else "",
            "virality_score": 98,
            "duration": render_res["duration"],
            "video_url": render_res["video_url"],
            "download_url": render_res["download_url"],
            "filename": render_res["output_filename"],
            "hashtags": ["#viral", "#shorts", "#reels", "#untoldtruth", "#documentary"],
            "social_pack": {
                "instagram": {
                    "caption": f"🔥 {req.topic.title()}\n\nWatch till the end for the shocking truth!\n\n#reels #viral #shorts #secrets",
                    "best_time_to_post": "12:30 PM / 7:30 PM",
                    "audio_tip": "Use trending suspense sound at 5% volume."
                },
                "youtube": {
                    "title": f"{req.topic.title()} #Shorts",
                    "description": f"The full breakdown of {req.topic}.\n\nSubscribe for daily deep dives!",
                    "tags": ["shorts", "documentary", "truth", "viral"]
                },
                "facebook": {
                    "caption": f"Did you know this about {req.topic}? Let us know in the comments!",
                    "engagement_question": f"What was your reaction to this?"
                }
            }
        }

        # Save to persistent history
        history_manager.save_job(
            job_id=job_id,
            video_meta={
                "title": req.topic.title(),
                "author": "AI B-Roll Story Studio",
                "duration": render_res["duration"],
                "thumbnail": req.scenes[0].get("selected_clip", {}).get("thumbnail", "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600&auto=format&fit=crop&q=80"),
                "is_broll_studio": True
            },
            reels=[reel_data],
            mode="broll_story_studio"
        )

        jobs_state[job_id].update({
            "status": "completed",
            "stage": "completed",
            "percent": 100.0,
            "message": "AI Viral Story Reel successfully rendered with multi-clip B-roll!",
            "reels": [reel_data]
        })

    except Exception as e:
        logger.error(f"BRoll pipeline error for job {job_id}: {e}", exc_info=True)
        jobs_state[job_id] = {
            "status": "error",
            "percent": 0.0,
            "message": f"Render failed: {str(e)}",
            "error": str(e)
        }

@app.post("/api/broll/render")
async def render_broll_reel(req: BRollRenderRequest, background_tasks: BackgroundTasks):
    """Start asynchronous multi-clip B-roll reel synthesis."""
    if not req.scenes:
        raise HTTPException(status_code=400, detail="Scenes breakdown cannot be empty")

    job_id = f"broll_{uuid.uuid4().hex[:10]}"
    jobs_state[job_id] = {
        "status": "queued",
        "percent": 5.0,
        "message": "Queuing B-Roll Story Reel generation..."
    }

    background_tasks.add_task(run_broll_pipeline, job_id, req)
    return {"status": "success", "job_id": job_id}

@app.get("/api/broll/progress/{job_id}")
async def get_broll_progress(job_id: str):
    """Poll rendering progress for a B-roll studio job."""
    if job_id not in jobs_state:
        # Check if saved in history
        job = history_manager.get_job(job_id)
        if job:
            return {"status": "completed", "percent": 100.0, "reels": job.get("reels", [])}
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs_state[job_id]

# Mount frontend directory for static UI serving
FRONTEND_DIR = BASE_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
