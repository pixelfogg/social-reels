import os
import sys
import subprocess
from pathlib import Path

# Configure utf-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

def check_and_install_dependencies():
    """Verify core dependencies are present; install if missing."""
    required = [
        "fastapi", "uvicorn", "pydantic", "yt_dlp", "faster_whisper",
        "imageio_ffmpeg", "cv2", "edge_tts", "mutagen", "requests"
    ]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
            
    if missing:
        print(f"[*] Missing dependencies detected: {missing}")
        print("[*] Automatically installing missing packages...")
        req_file = BASE_DIR / "requirements.txt"
        if req_file.exists():
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_file)], check=True)
        else:
            subprocess.run([sys.executable, "-m", "pip", "install"] + missing, check=True)
        print("[*] All dependencies installed successfully!\n")

def ensure_storage_structure():
    """Ensure all required runtime storage folders exist."""
    dirs = [
        BASE_DIR / "storage" / "downloads",
        BASE_DIR / "storage" / "outputs",
        BASE_DIR / "storage" / "temp",
        BASE_DIR / "storage" / "clips",
        BASE_DIR / "backend" / "assets" / "fonts"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    print("=" * 65)
    print("  [ReelsAI Studio] YouTube to Viral Shorts & Reels Engine")
    print("=================================================================")
    
    # 1. Check dependencies
    check_and_install_dependencies()
    
    # 2. Ensure storage folders
    ensure_storage_structure()
    
    # 3. Ensure fonts are present
    try:
        from backend.download_fonts import ensure_fonts
        ensure_fonts()
    except Exception:
        pass
        
    # 4. Import & Start Web App
    import uvicorn
    
    print("\nStarting Web Studio Server...")
    print("  >> Local Web App: http://localhost:8000")
    print("  >> API Docs:      http://localhost:8000/docs\n")
    
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)
