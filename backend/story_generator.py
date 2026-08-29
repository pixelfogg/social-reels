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

        # Story Style 1: रहस्यमयी कहानी (The Untold Story)
        story_1_script = (
            f"क्या आप जानते हैं कि {entity} की असली सफलता का रहस्य क्या था? "
            f"{year} में जब पूरी दुनिया सोच रही थी कि सब कुछ खत्म हो गया है, "
            f"तब एक ऐसा मास्टरप्लान बनाया गया जिसने पूरे खेल को बदल दिया। "
            f"लोग सिर्फ उनकी कामयाबी देखते हैं, लेकिन इसके पीछे के संघर्ष और गुप्त रणनीति को बहुत कम लोग जानते हैं। "
            f"असली सबक यह है कि जब भी परिस्थितियां आपके खिलाफ हों, तो हार मानने के बजाय अपना नजरिया बदलें। "
            f"{random.choice(HINDI_CTAS)}"
        )
        stories.append({
            "id": "story_1",
            "style": "untold_story",
            "title": f"{entity} का सबसे बड़ा रहस्य 🔥",
            "hook": "क्या आप जानते हैं इसके पीछे का असली सच? 🤯",
            "script": story_1_script,
            "visual_keywords": [f"{entity} portrait", "secret plan whiteboard", "struggle dark room", "success victory crowd", "motivation spark"],
            "language": "hi"
        })

        # Story Style 2: 1 मिनट की मास्टरक्लास (1-Minute Masterclass)
        story_2_script = (
            f"अगर आप जीवन में कुछ बड़ा हासिल करना चाहते हैं, तो {entity} का यह 1 नियम हमेशा याद रखें। "
            f"अधिकांश लोग अपनी 90% ऊर्जा उन चीजों पर बर्बाद करते हैं जो उनके नियंत्रण में नहीं होतीं। "
            f"लेकिन असली लीडर्स सिर्फ अपने फोकस और अनुशासन पर काम करते हैं। "
            f"जब आप अपने लक्ष्य के प्रति 100% समर्पित हो जाते हैं, तो असफलता भी आपके लिए एक नया अवसर बन जाती है। "
            f"इस बात को हमेशा गांठ बांध लें। {random.choice(HINDI_CTAS)}"
        )
        stories.append({
            "id": "story_2",
            "style": "masterclass",
            "title": f"1 मिनट में जीवन बदलने वाला नियम 💡",
            "hook": "यह 1 नियम आपका नजरिया बदल देगा 🚀",
            "script": story_2_script,
            "visual_keywords": ["laser focus target", "discipline clock", "mindset brain light", "growth chart upward", "leader presentation"],
            "language": "hi"
        })

        # Story Style 3: सबसे बड़ी गलती (The Costly Mistake)
        story_3_script = (
            f"यह एक ऐसी गलती है जिसे 99% लोग अपनी जिंदगी में दोहराते हैं। "
            f"{entity} ने अपने करियर के सबसे कठिन समय में एक कड़ा फैसला लिया था। "
            f"जब समाज ने उन पर शक किया, तब उन्होंने खुद पर भरोसा करना नहीं छोड़ा। "
            f"अगर आप भी दूसरों के डर के हिसाब से अपने फैसले लेंगे, तो कभी अपने असली सामर्थ्य तक नहीं पहुंच पाएंगे। "
            f"डर से आगे बढ़िए और अपने काम पर भरोसा रखिए। {random.choice(HINDI_CTAS)}"
        )
        stories.append({
            "id": "story_3",
            "style": "costly_mistake",
            "title": f"99% लोग यह भारी गलती करते हैं ⚠️",
            "hook": "क्या आप भी यही गलती कर रहे हैं? 🛑",
            "script": story_3_script,
            "visual_keywords": ["danger warning sign", "doubt confusion face", "courage determination", "victory celebration", "follow dream path"],
            "language": "hi"
        })

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
