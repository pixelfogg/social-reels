# 🎬 ReelsAI Studio — Automated YouTube to Viral Shorts & Reels

<div align="center">

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![AI Audio](https://img.shields.io/badge/AI_Audio-Edge_TTS-8E75C4?style=for-the-badge)](https://github.com/rany2/edge-tts)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg?style=for-the-badge)](https://github.com/pixelfogg/social-reels/pulls)

</div>

> **AI-Powered Short-Form Production Engine with Natural Hindi Neural Narration, 10–15 Highlight Extraction, Animated Karaoke Captions, and Multi-Platform Social SEO Packages.**

---

## 🌟 Key Features

### 1. 🛡️ Transformative Hindi Mini-Doc Mode (100% Monetizable & Copyright Shield)
- **Zero Audio Content ID**: Strips third-party audio waveforms and replaces them with neural narration.
- **Natural Hindi Voices**: Powered by `hi-IN-MadhurNeural` (Deep Documentary Male) and `hi-IN-SwaraNeural` (Dynamic Storyteller Female).
- **Original Viral Scripts**: Converts transcripts into 30–45s storytelling scripts (*Untold Story, 1-Min Masterclass, Costly Mistake*).
- **Multi-Source Visual Montage**: Slices 3-second micro-clips with 1.04x speed ramp and dynamic zoom, interleaved with ambient music and sound effects.

### 2. 🎬 Direct Highlights Mode (10–15 Reels per Video)
- **Intelligent Virality Scoring**: Scans entire video timelines to discover top hooks, high-energy punchlines, and key lessons.
- **Batch Reel Generation**: Extracts 1, 3, 5, 8, 10, 12, or 15 distinct, non-overlapping reels from any video.
- **Dynamic 9:16 Vertical Framing**: Blurred background canvas, speaker face reframing, or center crop.

### 3. ✨ Animated Karaoke Subtitles (Devanagari & Latin)
- **Word-Level Synchronization**: Active word scale pop animation (`115%`) and custom palettes (*Hormozi Gold, MrBeast Green, Submagic Violet, Cyberpunk Cyan*).
- **Platform Bottom Safe Zone**: Subtitles default to the bottom center (`280px` margin) to avoid overlapping UI controls on Instagram, TikTok, and YouTube Shorts.
- **Universal Font Stacks**: Native Devanagari Hindi font rendering (`Nirmala UI / Segoe UI Black`).

### 4. 📱 Ready-to-Post Multi-Platform Virality Packs
- **📸 Instagram Reels**: Hook, storytelling caption, CTA, 15+ curated hashtags, audio mixing tip & best posting hours.
- **🔴 YouTube Shorts**: High-CTR title (<60 chars with `#Shorts`), SEO keyword description, tags list, and pinned comment prompt.
- **🔵 Facebook Reels**: Provocative discussion headline and engagement questions.
- **📦 1-Click Export**: Download all reels and platform text files as a single ZIP bundle.

---

## 🚀 Quickstart Guide

### Prerequisites
- Python 3.10+
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/pixelfogg/social-reels.git
   cd social-reels
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate   # Windows
   # source .venv/bin/activate  # Linux/macOS
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the Studio:**
   ```bash
   python run_studio.py
   # Or on Windows, double click start.bat
   ```

5. **Open in Browser:**
   Navigate to [http://localhost:8000](http://localhost:8000)

---

## 🛠️ Tech Stack & Architecture

- **Backend**: FastAPI, Uvicorn, Pydantic
- **Speech Recognition**: Faster-Whisper (CTranslate2, Greedy CPU Acceleration)
- **Neural Voice Synthesis**: Edge-TTS (Microsoft Azure Neural Voices)
- **Video & Audio Processing**: FFmpeg 7.1, ImageIO-FFmpeg, OpenCV
- **Subtitle Generation**: Custom Advanced SubStation Alpha (`.ass`) Engine
- **Frontend**: Vanilla HTML5, CSS3 Glassmorphism, JavaScript, Lucide Icons

---

## 📁 Repository Structure

```
├── backend/
│   ├── app.py                      # FastAPI routes & pipeline orchestration
│   ├── config.py                   # Paths, directories & FFmpeg binary resolution
│   ├── downloader.py               # yt-dlp high-speed video streamer
│   ├── transcriber.py              # Faster-whisper word-level transcription
│   ├── analyzer.py                 # Viral hook discovery & social pack generator
│   ├── voice_engine.py             # Neural TTS & timestamp alignment
│   ├── story_generator.py          # Natural Hindi script & narrative generator
│   ├── stock_fetcher.py            # B-roll & procedural motion layer generator
│   ├── video_processor.py          # 9:16 vertical crop & ASS subtitle burner
│   ├── transformative_processor.py # Multi-source short compositor
│   └── caption_engine.py           # Animated ASS karaoke subtitle engine
├── frontend/
│   ├── index.html                  # Glassmorphic studio UI
│   ├── css/style.css               # Modern dark UI design system
│   └── js/app.js                   # Reactive player, trimmer & social switcher
├── storage/                        # Downloads, outputs, and temporary files
├── requirements.txt                # Python package dependencies
├── run_studio.py                   # Production launcher
├── start.bat                       # 1-click Windows launcher
└── README.md                       # Documentation
```

---

## 📄 License
MIT License. Built for creators and developers.
