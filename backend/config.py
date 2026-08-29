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
    """Find FFmpeg binary from imageio-ffmpeg or system PATH, ensuring ffmpeg.exe is created."""
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(ffmpeg_exe):
            bin_dir = Path(ffmpeg_exe).parent
            std_ffmpeg = bin_dir / "ffmpeg.exe"
            if not std_ffmpeg.exists():
                import shutil
                try:
                    shutil.copy2(ffmpeg_exe, std_ffmpeg)
                except Exception:
                    pass
            # Also copy to .venv/Scripts if exists
            venv_scripts = BASE_DIR / ".venv" / "Scripts" / "ffmpeg.exe"
            if venv_scripts.parent.exists() and not venv_scripts.exists():
                import shutil
                try:
                    shutil.copy2(ffmpeg_exe, venv_scripts)
                except Exception:
                    pass
            return str(std_ffmpeg) if std_ffmpeg.exists() else ffmpeg_exe
    except Exception:
        pass
    
    # Fallback to 'ffmpeg' in PATH
    return "ffmpeg"

def get_ffprobe_path() -> str:
    """Find FFprobe binary or derive from ffmpeg path."""
    ffmpeg_path = get_ffmpeg_path()
    if ffmpeg_path != "ffmpeg":
        ffprobe_cand = Path(ffmpeg_path).parent / "ffprobe.exe"
        if ffprobe_cand.exists():
            return str(ffprobe_cand)
    return "ffprobe"

FFMPEG_PATH = get_ffmpeg_path()
FFPROBE_PATH = get_ffprobe_path()

# Add ffmpeg directory to PATH so subprocesses & yt-dlp can find it easily
ffmpeg_bin_dir = str(Path(FFMPEG_PATH).parent)
if ffmpeg_bin_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{ffmpeg_bin_dir};{os.environ.get('PATH', '')}"

# Default Whisper Model Configuration
DEFAULT_WHISPER_MODEL = "base"  # options: tiny, base, small, medium

# Video Format Defaults
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
DEFAULT_FPS = 30
