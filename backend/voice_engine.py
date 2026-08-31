import os
import re
import json
import asyncio
import logging
import subprocess
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
import edge_tts
from backend.config import TEMP_DIR, FFMPEG_PATH, FFPROBE_PATH, ELEVENLABS_API_KEY
from backend.transcriber import Transcriber

logger = logging.getLogger("videogen.voice_engine")

SUPPORTED_VOICES = [
    {
        "id": "en-US-AndrewMultilingualNeural",
        "name": "Andrew",
        "gender": "Male",
        "language": "en",
        "label": "🎙️ Andrew — Warm, Authentic, Human Conversational (Multilingual)",
        "sample_text": "Here is the exact truth behind this story that nobody talks about."
    },
    {
        "id": "en-US-BrianMultilingualNeural",
        "name": "Brian",
        "gender": "Male",
        "language": "en",
        "label": "🎙️ Brian — Natural, Casual, Sincere Storyteller (Multilingual)",
        "sample_text": "When you look closely at what happened, everything begins to make sense."
    },
    {
        "id": "en-US-AvaMultilingualNeural",
        "name": "Ava",
        "gender": "Female",
        "language": "en",
        "label": "🎙️ Ava — Expressive, Engaging Human Storyteller (Multilingual)",
        "sample_text": "Did you know that one simple decision changed the course of history forever?"
    },
    {
        "id": "en-US-GuyNeural",
        "name": "Guy",
        "gender": "Male",
        "language": "en",
        "label": "🎙️ Guy — Passionate Deep Documentary Filmmaker",
        "sample_text": "This wasn't just an accident. It was the result of a calculated chain of events."
    },
    {
        "id": "en-IN-NeerjaExpressiveNeural",
        "name": "Neerja",
        "gender": "Female",
        "language": "en-IN",
        "label": "🎙️ Neerja — Expressive Indian English & Hinglish Narrator",
        "sample_text": "Let us explore the incredible strategy behind this unprecedented breakthrough."
    },
    {
        "id": "hi-IN-MadhurNeural",
        "name": "Madhur (मधुर)",
        "gender": "Male",
        "language": "hi",
        "label": "🎙️ Madhur — Deep Hindi Documentary (Male)",
        "sample_text": "नमस्ते, आज हम जानेंगे एक ऐसी कहानी जिसने पूरी दुनिया को बदल कर रख दिया।"
    },
    {
        "id": "hi-IN-SwaraNeural",
        "name": "Swara (स्वरा)",
        "gender": "Female",
        "language": "hi",
        "label": "🎙️ Swara — Emotive Hindi Storyteller (Female)",
        "sample_text": "क्या आप जानते हैं कि सबसे बड़े सफल लोगों की सबसे गुप्त आदत क्या होती है?"
    },
    {
        "id": "en-GB-RyanNeural",
        "name": "Ryan",
        "gender": "Male",
        "language": "en-GB",
        "label": "🎙️ Ryan — Deep British Cinematic Narrative",
        "sample_text": "Beneath the surface of this discovery lies an extraordinary hidden reality."
    },
    {
        "id": "en-US-ChristopherNeural",
        "name": "Christopher",
        "gender": "Male",
        "language": "en",
        "label": "🎙️ Christopher — Authoritative Documentary Voice",
        "sample_text": "Here is the untold truth that most people will never discover."
    },
    {
        "id": "eleven_adam",
        "name": "Adam (ElevenLabs)",
        "gender": "Male",
        "language": "en",
        "label": "💎 ElevenLabs Adam — Ultra-Realistic Studio Human Voice",
        "sample_text": "This is true studio quality narration with full human emotional range."
    },
    {
        "id": "eleven_rachel",
        "name": "Rachel (ElevenLabs)",
        "gender": "Female",
        "language": "en",
        "label": "💎 ElevenLabs Rachel — Ultra-Realistic Narrative Voice",
        "sample_text": "Welcome to an in-depth exploration of this extraordinary topic."
    }
]

class VoiceEngine:
    def __init__(self, transcriber: Optional[Transcriber] = None):
        self.transcriber = transcriber or Transcriber(model_size="base")

    def _format_natural_human_script(self, text: str) -> str:
        """Cleans and formats script for fluent, natural human speech prosody."""
        t = re.sub(r'\s+', ' ', text).strip()
        # Remove awkward repeated punctuation
        t = re.sub(r'[\.]{2,}', '.', t)
        # Ensure clean spacing after punctuation
        t = re.sub(r'([,\.\?!।])([^\s])', r'\1 \2', t)
        return t

    def _apply_studio_voice_mastering(self, raw_audio_path: str, mastered_audio_path: str):
        """
        Applies a professional studio vocal mastering chain:
        1. Highpass at 75Hz (eliminates sub-audible rumble/plosives)
        2. Warmth EQ (+2.8dB at 220Hz for rich vocal body)
        3. Presence EQ (+2.2dB at 3.5kHz for crisp articulation)
        4. De-harshness filter (-2.0dB at 7.5kHz removes metallic digital edge)
        5. Studio Vocal Compression (compand for smooth podcast/broadcast level)
        """
        try:
            audio_filter = (
                "highpass=f=75,"
                "equalizer=f=220:t=q:w=1.2:g=2.8,"
                "equalizer=f=3500:t=q:w=1.0:g=2.2,"
                "equalizer=f=7500:t=q:w=1.5:g=-2.0,"
                "compand=attacks=0.015:decays=0.08:points=-80/-80|-30/-18|-12/-6|0/-1:gain=2.0,"
                "volume=1.08"
            )
            cmd = [
                FFMPEG_PATH, "-y",
                "-i", raw_audio_path,
                "-af", audio_filter,
                "-c:a", "libmp3lame",
                "-b:a", "192k",
                mastered_audio_path
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            if Path(mastered_audio_path).exists() and Path(mastered_audio_path).stat().st_size > 1000:
                logger.info(f"Successfully mastered voice with Studio Vocal Chain -> {mastered_audio_path}")
                return True
        except Exception as e:
            logger.warning(f"Voice mastering filter bypassed (using raw audio): {e}")
        return False

    async def _generate_edge_tts(self, text: str, voice: str, output_path: str, rate: str = "+0%", pitch: str = "+0Hz"):
        """Call edge_tts to synthesize speech."""
        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
        await communicate.save(output_path)

    def _generate_elevenlabs_tts(self, text: str, voice_id: str, output_path: str, api_key: Optional[str] = None) -> bool:
        """Call ElevenLabs API for hyper-realistic human voice generation."""
        key = api_key or ELEVENLABS_API_KEY
        if not key:
            return False

        # Map friendly IDs to ElevenLabs voice IDs
        eleven_voice_map = {
            "eleven_adam": "pNInz6obpgDQGcFmaJgB",
            "eleven_rachel": "21m00Tcm4TlvDq8ikWAM",
            "eleven_antoni": "ErXwobaYiN019PkySvjV",
            "eleven_josh": "TxGEqnHWrfWFTfGW9XjX"
        }
        target_voice = eleven_voice_map.get(voice_id, "pNInz6obpgDQGcFmaJgB")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{target_voice}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": key
        }
        body = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.50,
                "similarity_boost": 0.80,
                "style": 0.35,
                "use_speaker_boost": True
            }
        }

        try:
            logger.info(f"Synthesizing hyper-realistic human voice via ElevenLabs ({target_voice})...")
            res = requests.post(url, headers=headers, json=body, timeout=30)
            if res.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(res.content)
                logger.info(f"ElevenLabs synthesis complete ({len(res.content)} bytes)")
                return True
            else:
                logger.warning(f"ElevenLabs API returned {res.status_code}: {res.text[:120]}")
        except Exception as e:
            logger.warning(f"ElevenLabs TTS error: {e}")
        return False

    def _get_audio_duration_fast(self, audio_path: str) -> float:
        """Get exact duration of synthesized audio in seconds via FFmpeg banner parsing."""
        try:
            cmd = [FFMPEG_PATH, "-i", audio_path]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            match = re.search(r'Duration:\s*(\d+):(\d+):(\d+\.\d+)', res.stderr)
            if match:
                hours, mins, secs = match.groups()
                dur = int(hours) * 3600 + int(mins) * 60 + float(secs)
                logger.info(f"Exact synthesized audio duration: {dur:.2f}s")
                return dur
        except Exception as e:
            logger.warning(f"Failed to get audio duration via ffmpeg: {e}")
        return 30.0

    def generate_narration(
        self,
        script_text: str,
        voice_id: str = "en-US-AndrewMultilingualNeural",
        output_name: str = "narration",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        align_subtitles: bool = False,
        elevenlabs_api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synthesize realistic human neural voice audio with studio mastering and natural prosody.
        """
        raw_audio_path = str(TEMP_DIR / f"{output_name}_raw.mp3")
        mastered_audio_path = str(TEMP_DIR / f"{output_name}.mp3")
        
        # Clean script for authentic human speech delivery
        human_text = self._format_natural_human_script(script_text)
        logger.info(f"Generating human narration ({voice_id}): '{human_text[:75]}...'")

        # 1. Check for ElevenLabs
        success = False
        if voice_id.startswith("eleven_") or elevenlabs_api_key:
            success = self._generate_elevenlabs_tts(human_text, voice_id, raw_audio_path, api_key=elevenlabs_api_key)

        # 2. Fallback to Edge-TTS Expressive Neural Voice
        if not success:
            edge_voice = voice_id if not voice_id.startswith("eleven_") else "en-US-AndrewMultilingualNeural"
            asyncio.run(self._generate_edge_tts(human_text, edge_voice, raw_audio_path, rate=rate, pitch=pitch))

        if not os.path.exists(raw_audio_path) or os.path.getsize(raw_audio_path) == 0:
            raise RuntimeError("Failed to synthesize audio from Voice engine.")

        # 3. Apply Studio Vocal Mastering Chain
        mastered = self._apply_studio_voice_mastering(raw_audio_path, mastered_audio_path)
        final_audio_path = mastered_audio_path if mastered else raw_audio_path

        is_hindi = voice_id.startswith("hi-")
        lang_code = "hi" if is_hindi else "en"

        # Fast path if subtitles not aligned
        if not align_subtitles:
            fast_dur = self._get_audio_duration_fast(final_audio_path)
            return {
                "audio_path": final_audio_path,
                "duration": fast_dur,
                "words": [],
                "text": script_text,
                "voice_id": voice_id,
                "language": lang_code
            }

        # Otherwise transcribe for subtitle sync
        logger.info("Aligning word timestamps on synthesized audio with Whisper...")
        whisper_res = self.transcriber.transcribe(
            video_path=final_audio_path,
            language=lang_code
        )

        whisper_words = []
        for seg in whisper_res.get("segments", []):
            whisper_words.extend(seg.get("words", []))

        total_duration = whisper_res.get("duration", 0.0)
        raw_words = script_text.split()
        all_words = []
        
        if whisper_words and abs(len(whisper_words) - len(raw_words)) <= 5:
            w_count = len(whisper_words)
            r_count = len(raw_words)
            for idx, w in enumerate(raw_words):
                w_idx = min(w_count - 1, int(idx * (w_count / r_count)))
                w_item = whisper_words[w_idx]
                all_words.append({
                    "word": w,
                    "start": round(w_item["start"], 3),
                    "end": round(w_item["end"], 3),
                    "probability": 1.0
                })
        else:
            step = total_duration / max(1, len(raw_words))
            for idx, w in enumerate(raw_words):
                all_words.append({
                    "word": w,
                    "start": round(idx * step, 3),
                    "end": round((idx + 1) * step, 3),
                    "probability": 1.0
                })

        return {
            "audio_path": final_audio_path,
            "duration": total_duration,
            "words": all_words,
            "text": script_text,
            "voice_id": voice_id,
            "language": lang_code
        }

    @staticmethod
    def get_available_voices() -> List[Dict[str, Any]]:
        return SUPPORTED_VOICES

voice_engine = VoiceEngine()


