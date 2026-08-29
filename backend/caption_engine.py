import os
import re
import math
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.config import FONTS_DIR, TEMP_DIR

# Color presets in ASS BGR format (&HAABBGGRR)
# Note: In ASS hex, order is &H[Alpha][Blue][Green][Red]
COLOR_PALETTES = {
    "yellow_pop": {
        "primary": "&H00FFFFFF",      # White base
        "highlight": "&H0000E5FF",    # Vibrant Hormozi Gold/Yellow (&H00 + B:00 + G:E5 + R:FF)
        "outline": "&H00000000",      # Deep Black
        "shadow": "&H60000000"
    },
    "neon_green": {
        "primary": "&H00FFFFFF",
        "highlight": "&H0014FF38",    # Electric Neon Green
        "outline": "&H00000000",
        "shadow": "&H60000000"
    },
    "cyber_cyan": {
        "primary": "&H00FFFFFF",
        "highlight": "&H00FFF000",    # Electric Cyan
        "outline": "&H00000000",
        "shadow": "&H80502000"
    },
    "fire_orange": {
        "primary": "&H00FFFFFF",
        "highlight": "&H000A66FF",    # Vivid Flame Orange
        "outline": "&H00000000",
        "shadow": "&H60000000"
    },
    "submagic_purple": {
        "primary": "&H00FFFFFF",
        "highlight": "&H00FF38E0",    # Bright Violet / Magenta
        "outline": "&H001A0B2E",
        "shadow": "&H805E178C"
    },
    "minimal_clean": {
        "primary": "&H00F0F0F0",
        "highlight": "&H00FFFFFF",
        "outline": "&H00202020",
        "shadow": "&H40000000"
    }
}

THEMES = {
    "hormozi": {
        "name": "Hormozi Viral Pop",
        "font_name": "Nirmala UI",
        "font_file": "Nirmala.ttf",
        "font_size": 76,
        "uppercase": True,
        "outline_width": 7.5,
        "shadow_offset": 4.0,
        "palette": "yellow_pop",
        "words_per_line": 3,
        "scale_highlight": 115,  # 115% scale pop on active word
        "emoji_enabled": True
    },
    "mrbeast": {
        "name": "MrBeast Action",
        "font_name": "Segoe UI Black",
        "font_file": "seguibl.ttf",
        "font_size": 80,
        "uppercase": True,
        "outline_width": 9.0,
        "shadow_offset": 5.0,
        "palette": "neon_green",
        "words_per_line": 2,
        "scale_highlight": 120,
        "emoji_enabled": True
    },
    "submagic": {
        "name": "Submagic Glow",
        "font_name": "Nirmala UI",
        "font_file": "Nirmala.ttf",
        "font_size": 74,
        "uppercase": False,
        "outline_width": 6.5,
        "shadow_offset": 4.5,
        "palette": "submagic_purple",
        "words_per_line": 3,
        "scale_highlight": 112,
        "emoji_enabled": True
    },
    "cyberpunk": {
        "name": "Cyberpunk Neon",
        "font_name": "Segoe UI Black",
        "font_file": "seguibl.ttf",
        "font_size": 74,
        "uppercase": True,
        "outline_width": 7.0,
        "shadow_offset": 5.0,
        "palette": "cyber_cyan",
        "words_per_line": 3,
        "scale_highlight": 115,
        "emoji_enabled": True
    },
    "minimalist": {
        "name": "Minimalist Cinema",
        "font_name": "Nirmala UI",
        "font_file": "Nirmala.ttf",
        "font_size": 68,
        "uppercase": False,
        "outline_width": 5.0,
        "shadow_offset": 2.5,
        "palette": "minimal_clean",
        "words_per_line": 4,
        "scale_highlight": 105,
        "emoji_enabled": False
    }
}

KEYWORD_EMOJIS = {
    "money": "💰", "cash": "💵", "dollar": "💵", "dollars": "💵", "rich": "🤑",
    "secret": "🤫", "secrets": "🤫", "truth": "👁️", "lie": "🤥",
    "fire": "🔥", "crazy": "🤯", "insane": "🤯", "mind": "🧠",
    "winner": "🏆", "win": "🏆", "winning": "🏆", "success": "🚀",
    "rocket": "🚀", "grow": "📈", "growth": "📈", "fast": "⚡",
    "stop": "🛑", "warning": "⚠️", "danger": "🚨", "death": "💀",
    "love": "❤️", "time": "⏳", "clock": "⏰", "watch": "👀",
    "idea": "💡", "tip": "💡", "strategy": "🎯", "target": "🎯",
    "question": "❓", "why": "🤔", "best": "⭐", "super": "✨"
}

def format_ass_time(seconds: float) -> str:
    """Format seconds as ASS timestamp: H:MM:SS.cc"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"

class CaptionEngine:
    def __init__(self):
        pass

    def _group_words_into_phrases(self, words: List[Dict[str, Any]], words_per_phrase: int = 3) -> List[List[Dict[str, Any]]]:
        """Group consecutive word-timestamp items into natural short phrases."""
        if not words:
            return []

        phrases = []
        current_phrase = []

        for i, word_item in enumerate(words):
            current_phrase.append(word_item)
            word_text = word_item.get("word", "")

            # Check if this word ends a sentence or if we reached chunk limit
            has_punctuation = any(p in word_text for p in [".", "?", "!", ";", ","])
            reached_limit = len(current_phrase) >= words_per_phrase

            # Also break phrase on significant silence gap (> 0.6s)
            has_gap = False
            if i + 1 < len(words):
                gap = words[i+1]["start"] - word_item["end"]
                if gap > 0.6:
                    has_gap = True

            if has_gap or reached_limit or (has_punctuation and len(current_phrase) >= 2):
                phrases.append(current_phrase)
                current_phrase = []

        if current_phrase:
            phrases.append(current_phrase)

        return phrases

    def generate_ass_subtitles(
        self,
        words: List[Dict[str, Any]],
        output_ass_path: str,
        theme_name: str = "hormozi",
        position: str = "bottom",  # "bottom", "center", "top"
        custom_font_size: Optional[int] = None,
        custom_highlight_color: Optional[str] = None,
        enable_emojis: Optional[bool] = None
    ) -> str:
        """Generate styled ASS subtitle file with dynamic active-word pop animations."""
        theme = THEMES.get(theme_name, THEMES["hormozi"]).copy()
        palette_key = theme.get("palette", "yellow_pop")
        palette = COLOR_PALETTES.get(palette_key, COLOR_PALETTES["yellow_pop"]).copy()

        if custom_font_size:
            theme["font_size"] = custom_font_size
        if custom_highlight_color and custom_highlight_color in COLOR_PALETTES:
            palette = COLOR_PALETTES[custom_highlight_color]
        if enable_emojis is not None:
            theme["emoji_enabled"] = enable_emojis

        # Vertical Alignment and Margins
        # In ASS: Alignment 2 = bottom center, 5 = middle center, 8 = top center
        # Margin 280px places the subtitle in the optimal safe zone for Reels/Shorts/TikTok
        alignment_map = {
            "bottom": (2, 280),
            "center": (5, 0),
            "top": (8, 280)
        }
        align_code, margin_v = alignment_map.get(position, (2, 280))

        font_family = theme["font_name"]
        font_size = theme["font_size"]
        outline_w = theme["outline_width"]
        shadow_w = theme["shadow_offset"]
        scale_hi = theme["scale_highlight"]

        c_pri = palette["primary"]
        c_hi = palette["highlight"]
        c_out = palette["outline"]
        c_shd = palette["shadow"]

        ass_header = f"""[Script Info]
Title: Viral Reel Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_family},{font_size},{c_pri},&H000000FF,{c_out},{c_shd},-1,0,0,0,100,100,1,0,1,{outline_w},{shadow_w},{align_code},50,50,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        dialogue_lines = []
        phrases = self._group_words_into_phrases(words, words_per_phrase=theme.get("words_per_line", 3))

        for phrase in phrases:
            if not phrase:
                continue

            phrase_start = phrase[0]["start"]
            phrase_end = phrase[-1]["end"]
            
            # Add small trailing buffer so words don't flash off abruptly
            phrase_end = max(phrase_end, phrase_start + 0.3)

            # Check if any word in phrase triggers an emoji
            phrase_emoji = ""
            if theme.get("emoji_enabled", True):
                for w in phrase:
                    clean_w = w["word"].lower().strip(".,!?\"'")
                    if clean_w in KEYWORD_EMOJIS:
                        phrase_emoji = f" {KEYWORD_EMOJIS[clean_w]}"
                        break

            # Create an active dialogue event for each word's speaking duration
            for idx, active_word in enumerate(phrase):
                w_start = active_word["start"]
                w_end = active_word["end"]
                
                # Expand end time to next word's start or phrase end to avoid black flickers
                if idx + 1 < len(phrase):
                    w_end = min(phrase[idx + 1]["start"], w_start + 1.2)
                else:
                    w_end = max(w_end, phrase_end)

                if w_end <= w_start:
                    w_end = w_start + 0.2

                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                # Assemble the styled line with the current word popped and highlighted
                line_parts = []
                for j, word_item in enumerate(phrase):
                    raw_w = word_item["word"]
                    display_w = raw_w.upper() if theme.get("uppercase", True) else raw_w

                    if j == idx:
                        # Active pop word: Highlight color + scale boost
                        line_parts.append(
                            f"{{\\c{c_hi}&\\fscx{scale_hi}\\fscy{scale_hi}}}{display_w}{{\\c{c_pri}&\\fscx100\\fscy100}}"
                        )
                    else:
                        # Non-active word: standard primary color
                        line_parts.append(f"{{\\c{c_pri}&}}{display_w}")

                full_line = " ".join(line_parts) + phrase_emoji
                dialogue_lines.append(
                    f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{full_line}"
                )

        full_ass_content = ass_header + "\n".join(dialogue_lines) + "\n"

        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(full_ass_content)

        return output_ass_path
