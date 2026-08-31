import os
import sys
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
STORAGE_DIR = BASE_DIR / "storage"
DOWNLOADS_DIR = STORAGE_DIR / "downloads"
CLIPS_DIR = STORAGE_DIR / "clips"
OUTPUTS_DIR = STORAGE_DIR / "outputs"
TEMP_DIR = STORAGE_DIR / "temp"
FONTS_DIR = BACKEND_DIR / "assets" / "fonts"

# Ensure all directories exist
for directory in [DOWNLOADS_DIR, CLIPS_DIR, OUTPUTS_DIR, TEMP_DIR, FONTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# FFmpeg Executable Resolution
def get_ffmpeg_path() -> str:
    """Find FFmpeg binary from imageio-ffmpeg or system PATH, ensuring standard ffmpeg binary is created."""
    binary_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(ffmpeg_exe):
            bin_dir = Path(ffmpeg_exe).parent
            std_ffmpeg = bin_dir / binary_name
            if not std_ffmpeg.exists():
                import shutil
                try:
                    shutil.copy2(ffmpeg_exe, std_ffmpeg)
                    os.chmod(std_ffmpeg, 0o755)
                except Exception:
                    pass
            # Also copy to .venv bin/Scripts if exists
            venv_bin_dir = BASE_DIR / ".venv" / ("Scripts" if sys.platform == "win32" else "bin")
            venv_ffmpeg = venv_bin_dir / binary_name
            if venv_bin_dir.exists() and not venv_ffmpeg.exists():
                import shutil
                try:
                    shutil.copy2(ffmpeg_exe, venv_ffmpeg)
                    os.chmod(venv_ffmpeg, 0o755)
                except Exception:
                    pass
            if std_ffmpeg.exists():
                return str(std_ffmpeg)
            if venv_ffmpeg.exists():
                return str(venv_ffmpeg)
            return ffmpeg_exe
    except Exception:
        pass
    
    # Fallback to 'ffmpeg' in PATH
    return "ffmpeg"

def get_ffprobe_path() -> str:
    """Find FFprobe binary or derive from ffmpeg path."""
    binary_name = "ffprobe.exe" if sys.platform == "win32" else "ffprobe"
    ffmpeg_path = get_ffmpeg_path()
    if ffmpeg_path != "ffmpeg":
        ffprobe_cand = Path(ffmpeg_path).parent / binary_name
        if ffprobe_cand.exists():
            return str(ffprobe_cand)
    return "ffprobe"

FFMPEG_PATH = get_ffmpeg_path()
FFPROBE_PATH = get_ffprobe_path()

# Add ffmpeg directory and .venv/bin to PATH so subprocesses & yt-dlp can find it easily
ffmpeg_bin_dir = str(Path(FFMPEG_PATH).parent)
venv_bin_dir = str(BASE_DIR / ".venv" / ("Scripts" if sys.platform == "win32" else "bin"))
path_entries = os.environ.get("PATH", "").split(os.pathsep)

for p in [ffmpeg_bin_dir, venv_bin_dir]:
    if p and p not in path_entries and os.path.exists(p):
        os.environ["PATH"] = f"{p}{os.pathsep}{os.environ.get('PATH', '')}"

# Default Whisper Model Configuration
DEFAULT_WHISPER_MODEL = "base"  # options: tiny, base, small, medium

# Video Format Defaults
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
DEFAULT_FPS = 30

# Pexels Video API Configuration
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "Oo1Gtz4fL8HggUo5V0UaWQ2fLeyDsMAiZnJqfIgfknrWwTMiJ7oDYlOM")

# AI LLM & Voice API Keys (Gemini, OpenAI, Groq, ElevenLabs)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
