import os
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
try:
    import torch
    HAS_CUDA = torch.cuda.is_available()
except ImportError:
    HAS_CUDA = False

from backend.config import FFMPEG_PATH, TEMP_DIR, DEFAULT_WHISPER_MODEL

logger = logging.getLogger(__name__)

class Transcriber:
    def __init__(self, model_size: str = DEFAULT_WHISPER_MODEL):
        self.model_size = model_size
        self._model = None
        # Auto-detect device
        self.device = "cuda" if HAS_CUDA else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "int8"
        logger.info(f"Initialized Transcriber with model={model_size}, device={self.device}, compute_type={self.compute_type}")

    def _load_model(self):
        if self._model is None:
            logger.info(f"Loading faster-whisper model: {self.model_size} ({self.device})...")
            from faster_whisper import WhisperModel
            threads = os.cpu_count() or 4
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=threads,
                num_workers=2
            )
        return self._model

    def extract_audio(self, video_path: str, audio_path: Optional[str] = None, max_duration: Optional[float] = None) -> str:
        """Extract 16kHz mono audio from video for transcription, optionally limiting duration for faster analysis."""
        if audio_path is None:
            audio_path = str(TEMP_DIR / f"{Path(video_path).stem}_audio.wav")
        
        cmd = [FFMPEG_PATH, "-y"]
        if max_duration and max_duration > 0:
            cmd.extend(["-t", str(max_duration)])
        cmd.extend([
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            audio_path
        ])
        
        logger.info(f"Extracting audio: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg audio extraction failed: {result.stderr}")
            raise RuntimeError(f"Audio extraction failed: {result.stderr}")
            
        return audio_path

    def transcribe(
        self,
        video_path: str,
        language: Optional[str] = None,
        max_duration: Optional[float] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """Transcribe video audio and return segments with precise word-level timestamps."""
        if progress_callback:
            progress_callback({"status": "transcribing", "percent": 5, "message": "Extracting audio track..."})

        audio_path = self.extract_audio(video_path, max_duration=max_duration)

        if progress_callback:
            progress_callback({"status": "transcribing", "percent": 15, "message": f"Loading speech model ({self.model_size})..."})

        model = self._load_model()

        if progress_callback:
            progress_callback({"status": "transcribing", "percent": 25, "message": "Analyzing audio stream..."})

        segments_raw, info = model.transcribe(
            audio_path,
            language=language,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
            beam_size=1,  # Fast greedy decoding
            best_of=1,
            temperature=0.0,
            condition_on_previous_text=False
        )

        total_audio_duration = max(1.0, getattr(info, 'duration', 1.0))
        segments = []
        full_text_list = []
        all_words = []

        for seg_idx, segment in enumerate(segments_raw):
            seg_words = []
            if segment.words:
                for w in segment.words:
                    word_dict = {
                        "word": w.word.strip(),
                        "start": round(w.start, 3),
                        "end": round(w.end, 3),
                        "probability": round(w.probability, 3)
                    }
                    if word_dict["word"]:
                        seg_words.append(word_dict)
                        all_words.append(word_dict)

            seg_data = {
                "id": seg_idx,
                "start": round(segment.start, 3),
                "end": round(segment.end, 3),
                "text": segment.text.strip(),
                "words": seg_words
            }
            segments.append(seg_data)
            full_text_list.append(segment.text.strip())

            # Emit live progress for every audio segment transcribed
            if progress_callback and total_audio_duration > 0:
                cur_sec = min(total_audio_duration, segment.end)
                pct = 25.0 + (cur_sec / total_audio_duration) * 70.0
                cur_min = int(cur_sec // 60)
                cur_s = int(cur_sec % 60)
                tot_min = int(total_audio_duration // 60)
                tot_s = int(total_audio_duration % 60)
                progress_callback({
                    "status": "transcribing",
                    "percent": round(pct, 1),
                    "message": f"Transcribing audio: {cur_min:02d}:{cur_s:02d} / {tot_min:02d}:{tot_s:02d} ({round(cur_sec/total_audio_duration*100)}%)"
                })

        # Cleanup temporary audio file
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception:
            pass

        if progress_callback:
            progress_callback({"status": "transcribing", "percent": 100, "message": "AI Transcription complete!"})

        return {
            "language": info.language,
            "language_probability": round(info.language_probability, 3),
            "duration": round(info.duration, 2),
            "text": " ".join(full_text_list),
            "segments": segments,
            "words": all_words
        }
