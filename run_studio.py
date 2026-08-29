import os
import sys
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

import uvicorn
from backend.download_fonts import ensure_fonts

if __name__ == "__main__":
    print("=" * 65)
    print("  [AI Reels Studio] YouTube to Shorts & Reels with Animated Captions")
    print("=" * 65)
    
    # Ensure required fonts are present
    ensure_fonts()
    
    print("\nStarting Web Studio Server...")
    print("  >> Local Web App: http://localhost:8000")
    print("  >> API Docs:      http://localhost:8000/docs\n")
    
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)
