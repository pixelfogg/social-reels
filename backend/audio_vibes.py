import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from backend.config import FFMPEG_PATH, TEMP_DIR

logger = logging.getLogger("videogen.audio_vibes")

AUDIO_VIBES = {
    "original_authentic": {
        "id": "original_authentic",
        "name": "🎙️ Authentic Dialogue (No BGM)",
        "description": "Pure creator speech with zero background music for maximum authenticity.",
        "bgm_volume": 0.0,
        "pitch_shift": "+0Hz",
        "rate": "+0%"
    },
    "mystery_suspense": {
        "id": "mystery_suspense",
        "name": "🕵️‍♂️ Dark Mystery & Suspense",
        "description": "Deep atmospheric drone with suspenseful low-end tension for shocking reveals.",
        "bgm_volume": 0.16,
        "pitch_shift": "-2Hz",
        "rate": "+2%"
    },
    "phonk_cyberpunk": {
        "id": "phonk_cyberpunk",
        "name": "⚡ Cyberpunk & Phonk Energy",
        "description": "Dark synth bassline and punchy electronic pulse for high-retention tech & hustle reels.",
        "bgm_volume": 0.18,
        "pitch_shift": "+0Hz",
        "rate": "+5%"
    },
    "cinematic_hype": {
        "id": "cinematic_hype",
        "name": "🔥 Cinematic Action & Drama",
        "description": "Rising dramatic crescendo and powerful cinematic presence for epic storytelling.",
        "bgm_volume": 0.16,
        "pitch_shift": "+0Hz",
        "rate": "+4%"
    },
    "lofi_chill": {
        "id": "lofi_chill",
        "name": "☕ Smooth Lo-Fi & Narrative",
        "description": "Chill, relaxing chord progression for thoughtful life advice and deep podcast vibes.",
        "bgm_volume": 0.14,
        "pitch_shift": "-1Hz",
        "rate": "+0%"
    }
}

class AudioVibeEngine:
    def __init__(self):
        pass

    def get_vibe(self, vibe_id: str) -> Dict[str, Any]:
        return AUDIO_VIBES.get(vibe_id, AUDIO_VIBES["mystery_suspense"])

    def generate_background_track(self, vibe_id: str, duration: float, output_path: str) -> Optional[str]:
        """
        Synthesize a procedural, high-quality audio bed tailored to the selected vibe
        using specialized multi-oscillator FFmpeg audio filter chains.
        """
        vibe = self.get_vibe(vibe_id)
        if vibe["bgm_volume"] <= 0.0:
            return None

        dur = max(2.0, duration)

        if vibe_id == "mystery_suspense":
            # Deep atmospheric suspense D-minor chord + violin tension pulse + heartbeat sub-bass
            cmd = [
                FFMPEG_PATH, "-y",
                "-f", "lavfi", "-i", f"sine=frequency=73.42:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency=87.31:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency=110.0:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency=587.33:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency=45.0:duration={dur}",
                "-f", "lavfi", "-i", f"anoisesrc=d={dur}:c=brown:r=44100:a=0.01",
                "-filter_complex",
                "[0:a]volume=0.45,lowpass=f=180[bass];"
                "[1:a]tremolo=f=0.2:d=0.7,volume=0.30[f3];"
                "[2:a]tremolo=f=0.3:d=0.6,volume=0.30[a3];"
                "[3:a]tremolo=f=4.0:d=0.9,vibrato=f=3.0:d=0.3,volume=0.18,highpass=f=400[lead];"
                "[4:a]tremolo=f=1.0:d=0.95,volume=0.40,lowpass=f=100[kick];"
                "[5:a]bandpass=f=800:w=400,volume=0.10[air];"
                "[bass][f3][a3][lead][kick][air]amix=inputs=6:dropout_transition=2,"
                "aecho=0.8:0.88:80|160:0.35|0.25,"
                "volume=1.0[aout]",
                "-map", "[aout]",
                "-c:a", "aac",
                "-b:a", "192k",
                output_path
            ]
        elif vibe_id == "phonk_cyberpunk":
            # Driving synth bass + electronic lead arpeggio + rhythmic percussion
            cmd = [
                FFMPEG_PATH, "-y",
                "-f", "lavfi", "-i", f"sine=frequency=55:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency=110:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency=329.63:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency=440.0:duration={dur}",
                "-f", "lavfi", "-i", f"anoisesrc=d={dur}:c=pink:r=44100:a=0.025",
                "-filter_complex",
                "[0:a]volume=0.6,tremolo=f=2.0:d=0.8,lowpass=f=150[sub808];"
                "[1:a]volume=0.4,tremolo=f=4.0:d=0.7[synth1];"
                "[2:a]volume=0.25,tremolo=f=6.0:d=0.9,vibrato=f=4:d=0.4[lead1];"
                "[3:a]volume=0.20,tremolo=f=8.0:d=0.8[lead2];"
                "[4:a]highpass=f=6000,tremolo=f=8.0:d=0.95,volume=0.20[hats];"
                "[sub808][synth1][lead1][lead2][hats]amix=inputs=5:dropout_transition=1,"
                "volume=1.0[aout]",
                "-map", "[aout]",
                "-c:a", "aac",
                "-b:a", "192k",
                output_path
            ]
        elif vibe_id == "cinematic_hype":
            # Epic orchestral C-minor brass progression + sub-bass boom impacts
            cmd = [
                FFMPEG_PATH, "-y",
                "-f", "lavfi", "-i", f"sine=frequency=65.41:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency=130.81:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency=155.56:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency=196.00:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency=523.25:duration={dur}",
                "-f", "lavfi", "-i", f"anoisesrc=d={dur}:c=brown:r=44100:a=0.02",
                "-filter_complex",
                "[0:a]volume=0.55,lowpass=f=120[sub];"
                "[1:a]volume=0.35,tremolo=f=0.5:d=0.6[c3];"
                "[2:a]volume=0.30,tremolo=f=0.7:d=0.5[eb3];"
                "[3:a]volume=0.30,tremolo=f=0.9:d=0.5[g3];"
                "[4:a]volume=0.20,vibrato=f=2.0:d=0.5,highpass=f=400[top];"
                "[5:a]tremolo=f=0.25:d=0.9,bandpass=f=600:w=300,volume=0.25[sweep];"
                "[sub][c3][eb3][g3][top][sweep]amix=inputs=6:dropout_transition=2,"
                "aecho=0.8:0.9:120|240:0.4|0.3,"
                "volume=1.0[aout]",
                "-map", "[aout]",
                "-c:a", "aac",
                "-b:a", "192k",
                output_path
            ]
        else: # lofi_chill
            # Warm Rhodes 7th chord progression + vinyl warmth
            cmd = [
                FFMPEG_PATH, "-y",
                "-f", "lavfi", "-i", f"sine=frequency=110.0:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency=138.59:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency=164.81:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency=207.65:duration={dur}",
                "-f", "lavfi", "-i", f"anoisesrc=d={dur}:c=pink:r=44100:a=0.008",
                "-filter_complex",
                "[0:a]volume=0.40,lowpass=f=400[bass];"
                "[1:a]volume=0.30,vibrato=f=2.5:d=0.3,lowpass=f=1200[cs3];"
                "[2:a]volume=0.25,vibrato=f=2.0:d=0.3,lowpass=f=1200[e3];"
                "[3:a]volume=0.20,vibrato=f=2.5:d=0.4,lowpass=f=1400[gs3];"
                "[4:a]volume=0.12,bandpass=f=1500:w=800[vinyl];"
                "[bass][cs3][e3][gs3][vinyl]amix=inputs=5:dropout_transition=2,"
                "aecho=0.7:0.8:60|120:0.3|0.2,"
                "volume=1.0[aout]",
                "-map", "[aout]",
                "-c:a", "aac",
                "-b:a", "192k",
                output_path
            ]

        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return output_path if os.path.exists(output_path) else None
        except Exception as e:
            logger.warning(f"Could not generate procedural BGM: {e}")
            return None

audio_vibe_engine = AudioVibeEngine()

