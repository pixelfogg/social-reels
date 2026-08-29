import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import edge_tts
from backend.config import TEMP_DIR
from backend.transcriber import Transcriber

logger = logging.getLogger("videogen.voice_engine")

SUPPORTED_VOICES = [
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
        "label": "🎙️ Swara — Dynamic Hindi Storyteller (Female)",
        "sample_text": "क्या आप जानते हैं कि सबसे बड़े सफल लोगों की सबसे गुप्त आदत क्या होती है?"
    },
    {
        "id": "en-US-ChristopherNeural",
        "name": "Christopher",
        "gender": "Male",
        "language": "en",
        "label": "🎙️ Christopher — Deep Cinematic Story (Male)",
        "sample_text": "Here is the untold truth that most people will never discover."
    },
    {
        "id": "en-US-JennyNeural",
        "name": "Jenny",
        "gender": "Female",
        "language": "en",
        "label": "🎙️ Jenny — Clear Professional (Female)",
        "sample_text": "Watch this before you make your next big career decision."
    },
    {
        "id": "en-IN-PrabhatNeural",
        "name": "Prabhat",
        "gender": "Male",
        "language": "en-IN",
        "label": "🎙️ Prabhat — Indian English Narrator (Male)",
        "sample_text": "In this short breakdown, we analyze the secret framework behind massive success."
    }
]

class VoiceEngine:
    def __init__(self, transcriber: Optional[Transcriber] = None):
        self.transcriber = transcriber or Transcriber(model_size="base")

    async def _generate_audio_file(self, text: str, voice: str, output_path: str, rate: str = "+0%", pitch: str = "+0Hz"):
        """Call edge_tts to synthesize speech."""
        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
        await communicate.save(output_path)

    def generate_narration(
        self,
        script_text: str,
        voice_id: str = "hi-IN-MadhurNeural",
        output_name: str = "narration",
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> Dict[str, Any]:
        """
        Synthesize neural voice audio and run Whisper to generate precise word-level timestamps.
        """
        output_audio_path = str(TEMP_DIR / f"{output_name}.mp3")
        
        logger.info(f"Generating neural TTS with voice {voice_id} for script of length {len(script_text)}")
        asyncio.run(self._generate_audio_file(script_text, voice_id, output_audio_path, rate=rate, pitch=pitch))
        
        if not os.path.exists(output_audio_path) or os.path.getsize(output_audio_path) == 0:
            raise RuntimeError("Failed to synthesize audio from TTS engine.")

        # Determine language code for transcription
        is_hindi = voice_id.startswith("hi-")
        lang_code = "hi" if is_hindi else "en"

        # Transcribe the generated audio using Whisper to get exact word timestamps
        logger.info("Aligning word timestamps on synthesized audio with Whisper...")
        whisper_res = self.transcriber.transcribe(
            video_path=output_audio_path,
            language=lang_code
        )

        whisper_words = []
        for seg in whisper_res.get("segments", []):
            whisper_words.extend(seg.get("words", []))

        total_duration = whisper_res.get("duration", 0.0)

        # Map exact original script Devanagari words to timestamps
        raw_words = script_text.split()
        all_words = []
        
        if whisper_words and abs(len(whisper_words) - len(raw_words)) <= 5:
            # Interpolate whisper timings directly onto original Devanagari words
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
            # Uniform cadence distribution across raw words
            step = total_duration / max(1, len(raw_words))
            for idx, w in enumerate(raw_words):
                all_words.append({
                    "word": w,
                    "start": round(idx * step, 3),
                    "end": round((idx + 1) * step, 3),
                    "probability": 1.0
                })

        return {
            "audio_path": output_audio_path,
            "duration": total_duration,
            "words": all_words,
            "text": script_text,
            "voice_id": voice_id,
            "language": lang_code
        }

    @staticmethod
    def get_available_voices() -> List[Dict[str, Any]]:
        return SUPPORTED_VOICES
