import os
import urllib.request
from pathlib import Path
from backend.config import FONTS_DIR

FONT_URLS = {
    "Montserrat-ExtraBold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf",
    "Anton-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf",
    "BebasNeue-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf",
    "Roboto-Bold.ttf": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto%5Bwdth%2Cwght%5D.ttf"
}

import requests

def ensure_fonts():
    """Ensure standard viral fonts are downloaded for subtitle rendering."""
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    for font_name, url in FONT_URLS.items():
        font_path = FONTS_DIR / font_name
        if not font_path.exists() or font_path.stat().st_size < 1000:
            try:
                print(f"Downloading font {font_name}...")
                resp = requests.get(
                    url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'},
                    timeout=20
                )
                resp.raise_for_status()
                with open(font_path, 'wb') as out_file:
                    out_file.write(resp.content)
                print(f"Downloaded {font_name} ({font_path.stat().st_size} bytes)")
            except Exception as e:
                print(f"Could not download {font_name}: {e}. Will use system Arial/Impact.")

if __name__ == "__main__":
    ensure_fonts()
