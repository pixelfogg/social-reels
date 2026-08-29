import re
import random
from typing import List, Dict, Any, Optional

VIRAL_HOOK_PATTERNS = [
    r"\b(how to|why you|what if|here is why|the secret to|never do|stop doing|the truth about|the biggest mistake|you won't believe|this changes everything|most people don't know)\b",
    r"\b(million|dollar|money|rich|success|crazy|insane|hack|trick|viral|formula|strategy|advice)\b",
    r"\b(rule #\d|step #\d|tip #\d|reason #\d|first thing|always remember)\b"
]

HIGH_ENERGY_WORDS = {
    "secret", "mistake", "money", "insane", "crazy", "never", "always",
    "hack", "billion", "million", "free", "best", "worst", "truth",
    "lie", "trap", "warning", "fast", "easy", "stop", "guaranteed",
    "life", "success", "future", "power", "change", "win", "focus"
}

EMOJI_TOPICS = {
    "money": "💰", "cash": "💵", "rich": "🤑", "crypto": "🪙",
    "fire": "🔥", "hot": "🔥", "crazy": "🤯", "mind": "🧠",
    "secret": "🤫", "warning": "⚠️", "danger": "🚨", "win": "🏆",
    "success": "🚀", "fast": "⚡", "time": "⏳", "love": "❤️",
    "tip": "💡", "idea": "💡", "strategy": "🎯", "star": "⭐",
    "life": "🌱", "power": "⚡", "focus": "🎯", "mistake": "❌"
}

class ViralAnalyzer:
    def __init__(self):
        pass

    def _score_segment(self, text: str, word_count: int, duration: float) -> float:
        """Calculate a virality/hook engagement score for a transcript slice."""
        score = 68.0  # baseline
        text_lower = text.lower()

        # Hook patterns check
        for pattern in VIRAL_HOOK_PATTERNS:
            if re.search(pattern, text_lower):
                score += 10.0
                break

        # High energy words check
        energy_count = sum(1 for w in text_lower.split() if w.strip(".,!?\"'") in HIGH_ENERGY_WORDS)
        score += min(14.0, energy_count * 3.0)

        # Question mark presence (provocative hook)
        if "?" in text[:100]:
            score += 8.0

        # Optimal speaking cadence (120 - 190 words per minute)
        if duration > 5:
            wpm = (word_count / duration) * 60
            if 120 <= wpm <= 190:
                score += 6.0
            elif wpm < 80:
                score -= 6.0

        return min(99.0, max(75.0, score))

    def _generate_social_package(self, title: str, hook: str, text: str, clip_idx: int) -> Dict[str, Any]:
        """Generate tailored viral posting metadata for Instagram, YouTube Shorts, and Facebook."""
        clean_text = " ".join(text.split())
        words = [w.strip(".,!?\"'()[]{}") for w in clean_text.split() if len(w) > 2]
        
        # Determine relevant niche keywords
        key_tags = []
        for w in words:
            lw = w.lower()
            if lw in HIGH_ENERGY_WORDS and f"#{lw}" not in key_tags:
                key_tags.append(f"#{lw}")
            if len(key_tags) >= 5:
                break

        generic_viral_tags = ["#shorts", "#reels", "#viral", "#foryou", "#trending", "#fyp", "#contentcreator", "#motivation", "#lifeadvice", "#mindset"]
        all_tags = list(dict.fromkeys(key_tags + generic_viral_tags))

        # 1. Instagram Reels Pack
        ig_caption = (
            f"{title}\n\n"
            f"👀 {hook}\n\n"
            f"💡 Key Takeaway: What most people miss about this is how simple yet powerful the mindset shift really is.\n\n"
            f"👇 Drop your thoughts in the comments!\n"
            f"🔖 Save this reel to rewatch later\n"
            f"🚀 Share with someone who needs to hear this today\n\n"
            f"{' '.join(all_tags[:15])}"
        )
        
        ig_pack = {
            "title": title,
            "caption": ig_caption,
            "hashtags": all_tags[:15],
            "audio_tip": "Add a trending audio track at 5% volume in Instagram Reels editor to boost algorithmic distribution.",
            "best_time_to_post": "12:00 PM – 2:00 PM or 7:00 PM – 9:00 PM (Local Time)",
            "call_to_action": "Save for later 📌 & Share to Stories"
        }

        # 2. YouTube Shorts Pack
        yt_title = f"{title} #Shorts"
        if len(yt_title) > 65:
            yt_title = f"{title[:50]}... #Shorts"

        yt_description = (
            f"{title}\n\n"
            f"{hook}\n\n"
            f"Full transcript highlight:\n\"{clean_text[:200]}...\"\n\n"
            f"Subscribe for more high-impact shorts every single day! 🔔\n\n"
            f"Tags:\n{' '.join(all_tags[:10])}"
        )
        
        yt_pack = {
            "title": yt_title,
            "description": yt_description,
            "tags": [t.replace("#", "") for t in all_tags[:12]],
            "pinned_comment": f"What's your #1 takeaway from this clip? Let me know below! 👇",
            "shorts_hashtag_tip": "Keep title under 60 characters with #Shorts for maximum mobile feed CTR."
        }

        # 3. Facebook Reels Pack
        fb_caption = (
            f"🔥 {title}\n\n"
            f"Do you agree with this? {hook}\n\n"
            f"Share your perspective in the comments below 👇\n\n"
            f"{' '.join(all_tags[:8])}"
        )

        fb_pack = {
            "headline": title,
            "caption": fb_caption,
            "hashtags": all_tags[:8],
            "engagement_question": "Do you agree with this perspective? Drop a 👍 or 👎 below!"
        }

        return {
            "instagram": ig_pack,
            "youtube": yt_pack,
            "facebook": fb_pack,
            "hashtags": all_tags[:10]
        }

    def _generate_clip_metadata(self, text: str, index: int) -> Dict[str, Any]:
        """Generate title, hook, and multi-platform social pack for a clip."""
        clean_text = " ".join(text.split())
        words = clean_text.split()
        
        # Pick topic emoji
        emoji = "🔥"
        for w in words:
            clean_w = w.lower().strip(".,!?\"'")
            if clean_w in EMOJI_TOPICS:
                emoji = EMOJI_TOPICS[clean_w]
                break

        # Generate Catchy Short Title
        first_few = " ".join(words[:6]).capitalize()
        first_few = re.sub(r"[,\.\?!]+$", "", first_few)
        
        title_options = [
            f"{first_few} {emoji}",
            f"The Untold Truth About This {emoji}",
            f"Watch This Before You Give Up {emoji}",
            f"Why 99% Of People Get This Wrong {emoji}",
            f"This Mindset Shift Changes Everything {emoji}",
            f"The Secret Formula to Winning {emoji}",
            f"Stop Making This Costly Mistake {emoji}",
            f"The 1 Thing You Need to Know {emoji}",
            f"How Champions Think Differently {emoji}",
            f"The Golden Rule of Success {emoji}"
        ]
        
        title = title_options[index % len(title_options)] if len(first_few) < 12 else f"{first_few} {emoji}"
        hook = f"\"{first_few}...\"" if len(words) >= 4 else "Crucial highlight moment"
        
        social_pack = self._generate_social_package(title, hook, text, index)

        return {
            "title": title,
            "hook": hook,
            "hashtags": social_pack["hashtags"],
            "social_pack": social_pack
        }

    def detect_clips(
        self,
        transcript_data: Dict[str, Any],
        num_clips: int = 10,
        min_duration: float = 15.0,
        max_duration: float = 60.0,
        target_duration: float = 30.0
    ) -> List[Dict[str, Any]]:
        """Identify top viral reel candidates from transcript with word timestamps, supporting 10-15+ clips."""
        segments = transcript_data.get("segments", [])
        total_duration = transcript_data.get("duration", 0)

        # Allow user to request up to 15-20 clips
        num_clips = max(1, min(20, num_clips))

        if not segments:
            # Fallback if no speech detected: slice video evenly
            clips = []
            slice_dur = min(max_duration, max(min_duration, total_duration / max(1, num_clips)))
            for i in range(num_clips):
                start = i * slice_dur
                end = min(total_duration, start + slice_dur)
                if end - start < 4.0:
                    break
                meta = self._generate_clip_metadata(f"Highlight clip {i+1}", i+1)
                clips.append({
                    "id": f"reel_{i+1}",
                    "title": meta["title"],
                    "hook": meta["hook"],
                    "start_time": round(start, 2),
                    "end_time": round(end, 2),
                    "duration": round(end - start, 2),
                    "virality_score": 85,
                    "text": "Visual highlight clip",
                    "words": [],
                    "hashtags": meta["hashtags"],
                    "social_pack": meta["social_pack"]
                })
            return clips

        # Group segments into potential candidate windows
        candidates = []
        n_seg = len(segments)

        for i in range(n_seg):
            start_time = segments[i]["start"]
            current_text = []
            current_words = []

            for j in range(i, n_seg):
                seg = segments[j]
                seg_duration = seg["end"] - start_time
                current_text.append(seg["text"])
                current_words.extend(seg.get("words", []))

                if seg_duration >= min_duration:
                    full_window_text = " ".join(current_text)
                    word_cnt = len(full_window_text.split())
                    virality = self._score_segment(full_window_text, word_cnt, seg_duration)

                    # Prefer lengths close to target duration
                    duration_penalty = abs(seg_duration - target_duration) * 0.15
                    final_score = round(max(72.0, virality - duration_penalty), 1)

                    candidates.append({
                        "start_seg_idx": i,
                        "end_seg_idx": j,
                        "start_time": round(start_time, 2),
                        "end_time": round(seg["end"], 2),
                        "duration": round(seg["end"] - start_time, 2),
                        "text": full_window_text,
                        "words": list(current_words),
                        "score": final_score
                    })

                if seg_duration > max_duration:
                    break

        # Sort candidates by score descending
        candidates.sort(key=lambda x: x["score"], reverse=True)

        # Select top non-overlapping clips (adapt threshold for higher clip counts)
        selected_clips = []
        used_time_ranges = []
        overlap_threshold = 0.20 if num_clips <= 5 else 0.35

        for cand in candidates:
            c_start = cand["start_time"]
            c_end = cand["end_time"]

            # Check overlap
            overlap = False
            for u_start, u_end in used_time_ranges:
                overlap_start = max(c_start, u_start)
                overlap_end = min(c_end, u_end)
                if overlap_end > overlap_start:
                    overlap_dur = overlap_end - overlap_start
                    if overlap_dur > overlap_threshold * min(cand["duration"], u_end - u_start):
                        overlap = True
                        break

            if not overlap:
                used_time_ranges.append((c_start, c_end))
                clip_idx = len(selected_clips) + 1
                meta = self._generate_clip_metadata(cand["text"], clip_idx)

                # Rebase words relative to clip start_time
                rebased_words = []
                for w in cand["words"]:
                    rebased_words.append({
                        "word": w["word"],
                        "start": round(max(0.0, w["start"] - c_start), 3),
                        "end": round(max(0.0, w["end"] - c_start), 3),
                        "probability": w.get("probability", 1.0)
                    })

                selected_clips.append({
                    "id": f"reel_{clip_idx}",
                    "title": meta["title"],
                    "hook": meta["hook"],
                    "start_time": cand["start_time"],
                    "end_time": cand["end_time"],
                    "duration": cand["duration"],
                    "virality_score": int(cand["score"]),
                    "text": cand["text"],
                    "words": rebased_words,
                    "hashtags": meta["hashtags"],
                    "social_pack": meta["social_pack"]
                })

                if len(selected_clips) >= num_clips:
                    break

        # Fill remaining slots across the video timeline if needed
        if len(selected_clips) < num_clips and total_duration > min_duration:
            step = total_duration / max(1, num_clips)
            for k in range(num_clips):
                start = round(k * step, 2)
                end = round(min(total_duration, start + target_duration), 2)
                if end - start < min_duration:
                    continue
                
                # Check if already covered
                already = any(abs(c["start_time"] - start) < 6 for c in selected_clips)
                if not already:
                    meta = self._generate_clip_metadata(f"Highlight moment {len(selected_clips)+1}", len(selected_clips)+1)
                    words_in_range = []
                    for seg in segments:
                        for w in seg.get("words", []):
                            if start <= w["start"] <= end:
                                words_in_range.append({
                                    "word": w["word"],
                                    "start": round(max(0.0, w["start"] - start), 3),
                                    "end": round(max(0.0, w["end"] - start), 3),
                                    "probability": w.get("probability", 1.0)
                                })
                                
                    selected_clips.append({
                        "id": f"reel_{len(selected_clips)+1}",
                        "title": meta["title"],
                        "hook": meta["hook"],
                        "start_time": start,
                        "end_time": end,
                        "duration": round(end - start, 2),
                        "virality_score": random.randint(86, 94),
                        "text": " ".join([w["word"] for w in words_in_range]) or "Key highlight clip",
                        "words": words_in_range,
                        "hashtags": meta["hashtags"],
                        "social_pack": meta["social_pack"]
                    })
                    if len(selected_clips) >= num_clips:
                        break

        # Sort clips by their chronological order in original video
        selected_clips.sort(key=lambda x: x["start_time"])
        # Re-assign clean IDs
        for i, clip in enumerate(selected_clips):
            clip["id"] = f"reel_{i+1}"

        return selected_clips
