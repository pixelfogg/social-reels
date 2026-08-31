import re
import random
from typing import List, Dict, Any, Optional

HINDI_HOOKS = [
    "क्या आप जानते हैं कि इसके पीछे का असली सच क्या है? 🤯",
    "यह एक ऐसी बात है जो 99% लोग कभी नहीं समझ पाते। 🔥",
    "इतिहास में एक ऐसी घटना घटी जिसने सब कुछ बदल कर रख दिया। 🚀",
    "अगर आपको लगता है कि सफलता आसान है, तो यह कहानी जरूर सुनिए। 💡",
    "यह गलती लगभग हर कोई करता है, लेकिन इसे सुधारने का तरीका बहुत आसान है। ⚠️"
]

HINDI_CTAS = [
    "अगर आपको यह बात समझ आई, तो इस रील को अभी सेव करें और फॉलो करना न भूलें! 📌",
    "आपकी इस बारे में क्या राय है? कमेंट में जरूर बताएं! 👇",
    "इस वीडियो को अपने उस दोस्त के साथ शेयर करें जिसे इसकी सबसे ज्यादा जरूरत है! 🚀",
    "ऐसे ही और पावरफुल इनसाइट्स के लिए अभी फॉलो करें! 🔔"
]

class StoryGenerator:
    def __init__(self):
        pass

    def extract_core_entities_and_facts(self, transcript_text: str) -> Dict[str, Any]:
        """Extract key topics, names, and high-energy phrases from the transcript."""
        clean = " ".join(transcript_text.split())
        words = clean.split()
        
        # Look for numbers/years/money amounts
        years = re.findall(r"\b(19\d\d|20\d\d)\b", clean)
        money = re.findall(r"(\$\d+|\d+\s*(?:dollar|million|billion|crore|lakh))", clean, re.IGNORECASE)
        
        # Extract potential named entities (capitalized words)
        capitalized = [w.strip(".,!?\"'") for w in words if w and w[0].isupper() and len(w) > 3]
        common_exclude = {"This", "That", "When", "What", "There", "They", "Have", "With", "From", "About", "Then", "After", "Before", "Because"}
        entities = [e for e in capitalized if e not in common_exclude]
        
        key_entity = entities[0] if entities else "यह महान व्यक्ति"
        primary_year = years[0] if years else "शुरुआती दिनों में"
        
        return {
            "entity": key_entity,
            "year": primary_year,
            "money": money[0] if money else None,
            "total_words": len(words),
            "summary_excerpt": clean[:300]
        }

    def generate_hindi_stories(
        self,
        transcript_data: Dict[str, Any],
        num_stories: int = 3,
        style: str = "untold_story"
    ) -> List[Dict[str, Any]]:
        """Generate high-retention viral Hindi scripts based on video content."""
        transcript_text = transcript_data.get("text", "")
        if not transcript_text:
            segments = transcript_data.get("segments", [])
            transcript_text = " ".join([s.get("text", "") for s in segments])

        meta = self.extract_core_entities_and_facts(transcript_text)
        entity = meta["entity"]
        year = meta["year"]

        stories = []

        # Story Style 1: 🕵️‍♂️ रहस्य और अनसुने सच (Viral Mystery & Untold Story)
        story_1_script = (
            f"क्या आप जानते हैं कि {entity} के इस किस्से के पीछे का असली सच क्या है? "
            f"{year} में जब सब सोच रहे थे कि सब कुछ सामान्य है, "
            f"तब परदे के पीछे एक ऐसा गुप्त फैसला लिया गया जिसने इतिहास बदल कर रख दिया। "
            f"ज्यादातर लोग सिर्फ ऊपरी चमक-दमक देखते हैं, लेकिन जो रहस्य दबा रह गया वह रोंगटे खड़े कर देने वाला है। "
            f"असली सच्चाई हमेशा आपकी सोच से कहीं ज्यादा गहरी होती है। "
            f"{random.choice(HINDI_CTAS)}"
        )
        stories.append({
            "id": "story_1",
            "style": "viral_mystery",
            "title": f"{entity} का अनसुना काला सच 🕵️‍♂️",
            "hook": "यह सच्चाई जानकर आपके रोंगटे खड़े हो जाएंगे 🤯",
            "script": story_1_script,
            "visual_keywords": [f"{entity} portrait", "secret classified files", "dark investigation room", "shocked crowd", "mystery revelation"],
            "language": "hi"
        })

        # Story Style 2: 🎙️ कड़वा सच और बहस (Hot Takes & Controversial Debate)
        story_2_script = (
            f"यह एक ऐसी बात है जिसे कोई भी खुलकर स्वीकार नहीं करना चाहता। "
            f"{entity} ने जिस रास्ते को चुना, आज के 90% तथाकथित विशेषज्ञ उसे गलत बताते हैं। "
            f"लेकिन हकीकत यह है कि नियमों को तोड़े बिना कभी कोई नया साम्राज्य नहीं खड़ा हुआ। "
            f"अगर आप हर किसी को खुश करने की कोशिश करेंगे, तो अंत में आप खुद की पहचान खो देंगे। "
            f"क्या आप इस कड़वे सच को मानने की हिम्मत रखते हैं? {random.choice(HINDI_CTAS)}"
        )
        stories.append({
            "id": "story_2",
            "style": "hot_takes_debate",
            "title": f"यह कड़वा सच कोई नहीं बताएगा 🎙️",
            "hook": "99% लोग इस बात को मानने से डरते हैं 🔥",
            "script": story_2_script,
            "visual_keywords": ["podcast mic close up", "intense debate stage", "breaking rules rebellion", "confident leader", "fire explosion"],
            "language": "hi"
        })

        # Story Style 3: 🧠 माइंड-ब्लोइंग तकनीक और भविष्य (Tech & AI Breakthrough)
        story_3_script = (
            f"आने वाले कुछ ही सालों में हमारी पूरी दुनिया हमेशा के लिए बदलने वाली है। "
            f"{entity} ने जिस क्रांति की शुरुआत की, वह आज टेक्नोलॉजी का सबसे बड़ा टर्निंग पॉइंट बन चुकी है। "
            f"जो लोग आज इस तकनीक को समझकर अपना लेंगे, वे कल की दुनिया पर राज करेंगे। "
            f"और जो इसे नजरअंदाज करेंगे, वे इतिहास के पन्नों में खो जाएंगे। "
            f"भविष्य का हिस्सा बनिए, दर्शक मत बने रहिए। {random.choice(HINDI_CTAS)}"
        )
        stories.append({
            "id": "story_3",
            "style": "tech_breakthrough",
            "title": f"भविष्य की तकनीक जिसने सब हिला दिया 🧠",
            "hook": "अगले 2 सालों में यह सब कुछ बदल देगा ⚡",
            "script": story_3_script,
            "visual_keywords": ["cyberpunk hologram AI", "futuristic glowing circuit", "supercomputer data stream", "laser neural network", "space exploration"],
            "language": "hi"
        })

        # Story Style 4: 💰 करोड़ों का खेल (Wealth, Power & Money Secrets)
        story_4_script = (
            f"अमीरों और गरीबों के बीच केवल एक बुनियादी सोच का फर्क होता है। "
            f"{year} में {entity} के पास खोने के लिए कुछ नहीं था, लेकिन उन्होंने एक ऐसा वित्तीय दांव खेला जिसने उन्हें शीर्ष पर पहुंचा दिया। "
            f"आम इंसान सिर्फ मेहनत करता है, लेकिन असली दौलतमंद सिस्टम और लीवरेज का इस्तेमाल करते हैं। "
            f"पैसा समय के बदले नहीं, बल्कि आपके द्वारा पैदा की गई वैल्यू के बदले आता है। "
            f"इस फॉर्मूले को अपनी जिंदगी में उतारिए। {random.choice(HINDI_CTAS)}"
        )
        stories.append({
            "id": "story_4",
            "style": "wealth_secrets",
            "title": f"करोड़ों कमाने का गुप्त नियम 💰",
            "hook": "अमीर लोग यह बात किसी को नहीं सिखाते 🤑",
            "script": story_4_script,
            "visual_keywords": ["gold bullion coins", "luxury penthouse skyline", "financial stock chart green", "wealth power handshake", "diamond luxury"],
            "language": "hi"
        })

        # Story Style 5: ⚡ रोमांचक टर्निंग पॉइंट (High-Stakes Turning Point Drama)
        story_5_script = (
            f"जब चारों तरफ अंधेरा था और सबने उम्मीद छोड़ दी थी, तब {entity} ने इतिहास का सबसे साहसी फैसला लिया। "
            f"उस एक पल की झिझक सब कुछ बर्बाद कर सकती थी, लेकिन उन्होंने बिना डरे कदम आगे बढ़ाया। "
            f"यही वह पल था जिसने एक साधारण इंसान को महान बना दिया। "
            f"याद रखिए, आपकी किस्मत किसी और के हाथों में नहीं, आपके अपने साहसिक फैसलों में है। "
            f"{random.choice(HINDI_CTAS)}"
        )
        stories.append({
            "id": "story_5",
            "style": "action_story",
            "title": f"वह 1 सेकंड जिसने इतिहास पलट दिया ⚡",
            "hook": "इस टर्निंग पॉइंट ने पूरी बाजी पलट दी 🚀",
            "script": story_5_script,
            "visual_keywords": ["running through fire drama", "turning point clock countdown", "extreme courage face", "epic victory stadium", "lightning storm"],
            "language": "hi"
        })

        # Story Style 6: 💡 1 मिनट का सटीक सबक (1-Minute Masterclass)
        story_6_script = (
            f"अगर आप किसी भी क्षेत्र में टॉप 1% में आना चाहते हैं, तो {entity} का यह बुनियादी सिद्धांत याद रखें। "
            f"असफल लोग हर समस्या में बहाना ढूंढते हैं, जबकि सफल लोग हर चुनौती को अवसर में बदल देते हैं। "
            f"रोजाना सिर्फ 1% सुधार आपको साल के अंत में 37 गुना बेहतर बना देता है। "
            f"आज से ही शुरुआत कीजिए। {random.choice(HINDI_CTAS)}"
        )
        stories.append({
            "id": "story_6",
            "style": "masterclass",
            "title": f"1 मिनट में टॉप 1% बनने का फॉर्मूला 💡",
            "hook": "यह छोटा सा बदलाव आपकी जिंदगी बदल देगा 🎯",
            "script": story_6_script,
            "visual_keywords": ["laser focus target", "discipline clock", "mindset brain light", "growth chart upward", "leader presentation"],
            "language": "hi"
        })

        # Filter by style if requested, or return full curated set
        if style and style != "all" and any(s["style"] == style for s in stories):
            # Prioritize requested style
            stories.sort(key=lambda s: 0 if s["style"] == style else 1)

        # Add Social Posting Packs to each story
        for idx, s in enumerate(stories):
            s["social_pack"] = self._generate_hindi_social_pack(s["title"], s["hook"], s["script"])

        return stories[:num_stories]

    def _generate_hindi_social_pack(self, title: str, hook: str, script: str) -> Dict[str, Any]:
        """Generate high-ranking Hindi & Hinglish social packs with viral tags."""
        tags = ["#shorts", "#reels", "#hindi", "#hindimotivation", "#successmindset", "#viralreels", "#facts", "#gyan", "#trendingreels", "#inspiration"]

        # 1. Instagram Pack
        ig_caption = (
            f"🔥 {title}\n\n"
            f"👀 {hook}\n\n"
            f"💡 मुख्य सीख: जीवन में सबसे महत्वपूर्ण बात यह है कि आप विपरीत परिस्थितियों में कैसे प्रतिक्रिया देते हैं।\n\n"
            f"👇 आपकी इस पर क्या राय है? कमेंट में बताएं!\n"
            f"🔖 इस रील को बाद के लिए सेव करें\n"
            f"🚀 अपने दोस्तों के साथ शेयर करें\n\n"
            f"{' '.join(tags)}"
        )
        
        ig_pack = {
            "title": title,
            "caption": ig_caption,
            "hashtags": tags,
            "audio_tip": "Instagram Reels में 5% बैकग्राउंड वॉल्यूम पर ट्रेंडिंग हिंदी ऑडियो ऐड करें।",
            "best_time_to_post": "1:00 PM – 3:00 PM या 7:30 PM – 9:30 PM (IST)",
            "call_to_action": "Save & Share 📌"
        }

        # 2. YouTube Shorts Pack
        yt_title = f"{title} #Shorts"
        if len(yt_title) > 65:
            yt_title = f"{title[:48]}... #Shorts"

        yt_description = (
            f"{title}\n\n"
            f"{hook}\n\n"
            f"इस शॉर्ट में जानिए सफलता और मानसिकता का सबसे बड़ा रहस्य।\n\n"
            f"रोजाना ऐसी ही ज्ञानवर्धक और मोटिवेशनल शॉर्ट्स के लिए अभी सब्सक्राइब करें! 🔔\n\n"
            f"Tags:\n{' '.join(tags)}"
        )

        yt_pack = {
            "title": yt_title,
            "description": yt_description,
            "tags": [t.replace("#", "") for t in tags],
            "pinned_comment": "इस वीडियो से आपकी सबसे बड़ी सीख क्या रही? कमेंट में जरूर बताएं! 👇",
            "shorts_hashtag_tip": "#Shorts और #Hindi टैग का प्रयोग टाइटल में अवश्य करें।"
        }

        # 3. Facebook Reels Pack
        fb_caption = (
            f"💡 {title}\n\n"
            f"{hook}\n\n"
            f"क्या आप इस बात से सहमत हैं? अपनी राय कमेंट में जरूर साझा करें 👇\n\n"
            f"{' '.join(tags[:8])}"
        )

        fb_pack = {
            "headline": title,
            "caption": fb_caption,
            "hashtags": tags[:8],
            "engagement_question": "क्या आप इस दृष्टिकोण से सहमत हैं? हाँ (👍) या ना (👎) कमेंट करें!"
        }

        return {
            "instagram": ig_pack,
            "youtube": yt_pack,
            "facebook": fb_pack,
            "hashtags": tags
        }
