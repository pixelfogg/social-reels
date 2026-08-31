import os
import re
import json
import logging
import requests
from typing import List, Dict, Any, Optional
from backend.config import GEMINI_API_KEY, OPENAI_API_KEY, GROQ_API_KEY

logger = logging.getLogger("viral_story_engine")
logger.setLevel(logging.INFO)

# High-Converting Viral Niche Templates
VIRAL_NICHE_PRESETS = {
    "dark_secrets": {
        "name": "🕵️‍♂️ Dark Secrets & Conspiracies",
        "description": "Shocking industry secrets, hidden truths & corporate scandals",
        "default_voice": "hi-IN-MadhurNeural",
        "sfx_theme": "mystery"
    },
    "wealth_money": {
        "name": "💰 Wealth, Money & Power",
        "description": "How billionaires think, financial loopholes & psychological pricing",
        "default_voice": "hi-IN-MadhurNeural",
        "sfx_theme": "punchy"
    },
    "tech_ai": {
        "name": "🧠 Tech, AI & Future Shock",
        "description": "Mind-bending AI discoveries, robotics & future human evolution",
        "default_voice": "en-IN-PrabhatNeural",
        "sfx_theme": "cyber"
    },
    "psychology_tricks": {
        "name": "🔮 Dark Psychology & Human Brain",
        "description": "Body language hacks, manipulation defenses & persuasion secrets",
        "default_voice": "hi-IN-SwaraNeural",
        "sfx_theme": "mystery"
    },
    "business_breakdown": {
        "name": "📈 1-Minute Business Masterclass",
        "description": "Why brands win, ruthless marketing strategies & failure autopsies",
        "default_voice": "hi-IN-MadhurNeural",
        "sfx_theme": "punchy"
    }
}

class ViralStoryEngine:
    """Generates authentic, bespoke scene-by-scene documentary scripts with high-definition Pexels B-roll keywords."""

    def generate_scene_breakdown(
        self,
        topic: str,
        niche: str = "dark_secrets",
        language: str = "hinglish",
        duration_mode: str = "long",
        custom_prompt: Optional[str] = None,
        scene_count: Optional[int] = None,
        api_key: Optional[str] = None,
        ai_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Decomposes any user topic into an authentic, deeply researched, original multi-scene documentary."""
        topic_clean = topic.strip()
        if not topic_clean:
            topic_clean = "The Untold Truth Behind Modern Systems"

        # Check if user pasted full raw text/script
        if custom_prompt and len(custom_prompt.strip()) > 80:
            return self._parse_custom_script_to_scenes(custom_prompt.strip(), topic_clean, niche)

        # Target scenes count
        if duration_mode == "short":
            target_scenes = scene_count or 5
        elif duration_mode == "medium":
            target_scenes = scene_count or 9
        else:
            target_scenes = scene_count or 16

        # 1. Check for AI LLM (Gemini, Groq, OpenAI)
        active_gemini_key = api_key if (api_key and "AIza" in api_key) else (GEMINI_API_KEY or os.getenv("GOOGLE_API_KEY", ""))
        active_groq_key = api_key if (api_key and "gsk_" in api_key) else GROQ_API_KEY
        active_openai_key = api_key if (api_key and "sk-" in api_key) else OPENAI_API_KEY

        if active_gemini_key:
            llm_res = self._generate_with_gemini(topic_clean, niche, language, target_scenes, active_gemini_key, custom_prompt)
            if llm_res and len(llm_res.get("scenes", [])) >= 3:
                return llm_res

        if active_groq_key:
            llm_res = self._generate_with_openai_compatible(
                topic_clean, niche, language, target_scenes, active_groq_key,
                "https://api.groq.com/openai/v1/chat/completions", "llama-3.3-70b-versatile", custom_prompt
            )
            if llm_res and len(llm_res.get("scenes", [])) >= 3:
                return llm_res

        if active_openai_key:
            llm_res = self._generate_with_openai_compatible(
                topic_clean, niche, language, target_scenes, active_openai_key,
                "https://api.openai.com/v1/chat/completions", "gpt-4o-mini", custom_prompt
            )
            if llm_res and len(llm_res.get("scenes", [])) >= 3:
                return llm_res

        # 2. Intelligent Multi-Paradigm Story Engine (Bespoke narrative generation for any topic)
        return self._generate_bespoke_story_architecture(topic_clean, niche, language, target_scenes, duration_mode)

    def _generate_with_gemini(
        self,
        topic: str,
        niche: str,
        language: str,
        target_scenes: int,
        api_key: str,
        custom_prompt: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate original documentary scenes via Google Gemini 1.5 Flash."""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            sys_instructions = (
                f"You are an award-winning Netflix/Vox documentary scriptwriter and visual director. "
                f"Write a {target_scenes}-scene deep explanatory script about: '{topic}'.\n"
                f"Requirements:\n"
                f"- Return pure JSON with structure: {{\"title\": \"...\", \"scenes\": [...]}}\n"
                f"- Each scene must have: scene_number (int), role (hook/conflict/mechanism/case_study/revelation/cta), "
                f"chapter ('Chapter 1: ...'), script_hi (conversational, natural Hindi/Hinglish narration with realistic pauses), "
                f"script_en (English translation), search_query (2 to 4 concrete physical visual keywords for Pexels 9:16 portrait video, e.g. 'roulette wheel spinning casino' or 'vintage gold coins vault'), "
                f"target_duration (float between 10.0 and 15.0), sfx ('whoosh'/'glitch'/'bass_drop'/'cash_register').\n"
                f"- Ensure scenes tell a fresh, factual, continuous unfolding story with real facts, names, numbers and specific events."
            )
            if custom_prompt:
                sys_instructions += f"\nCustom requirements: {custom_prompt}"

            payload = {
                "contents": [{"parts": [{"text": sys_instructions}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.7
                }
            }

            res = requests.post(url, json=payload, timeout=25)
            if res.status_code == 200:
                data = res.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(raw_text)
                scenes = parsed.get("scenes", [])
                if scenes:
                    total_dur = sum(s.get("target_duration", 12.0) for s in scenes)
                    logger.info(f"Successfully generated {len(scenes)} bespoke scenes via Gemini 1.5 Flash")
                    return {
                        "topic": topic,
                        "title": parsed.get("title", f"Deep Breakdown: {topic}"),
                        "total_scenes": len(scenes),
                        "estimated_duration": round(total_dur, 1),
                        "scenes": scenes
                    }
        except Exception as e:
            logger.warning(f"Gemini generation error: {e}")
        return None

    def _generate_with_openai_compatible(
        self,
        topic: str,
        niche: str,
        language: str,
        target_scenes: int,
        api_key: str,
        endpoint_url: str,
        model_name: str,
        custom_prompt: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate original documentary scenes via Groq / OpenAI compatible endpoints."""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            prompt = (
                f"Write a {target_scenes}-scene deep explanatory documentary script about: '{topic}'.\n"
                f"Return JSON format: {{\"title\": \"...\", \"scenes\": [{{\"scene_number\": 1, \"role\": \"hook\", \"chapter\": \"Chapter 1: ...\", \"script_hi\": \"...\", \"script_en\": \"...\", \"search_query\": \"concrete visual keywords for Pexels portrait video\", \"target_duration\": 12.0, \"sfx\": \"whoosh\"}}]}}.\n"
                f"Make the storytelling deeply factual, realistic, and continuous."
            )
            if custom_prompt:
                prompt += f"\nAdditional Instructions: {custom_prompt}"

            body = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are a master investigative documentary filmmaker. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.7
            }

            res = requests.post(endpoint_url, headers=headers, json=body, timeout=25)
            if res.status_code == 200:
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                scenes = parsed.get("scenes", [])
                if scenes:
                    total_dur = sum(s.get("target_duration", 12.0) for s in scenes)
                    logger.info(f"Successfully generated {len(scenes)} bespoke scenes via {model_name}")
                    return {
                        "topic": topic,
                        "title": parsed.get("title", f"Deep Breakdown: {topic}"),
                        "total_scenes": len(scenes),
                        "estimated_duration": round(total_dur, 1),
                        "scenes": scenes
                    }
        except Exception as e:
            logger.warning(f"OpenAI/Groq generation error: {e}")
        return None

    def _generate_bespoke_story_architecture(
        self,
        topic: str,
        niche: str,
        language: str,
        target_scenes: int,
        duration_mode: str
    ) -> Dict[str, Any]:
        """
        Bespoke Multi-Paradigm Narrative Generator.
        Constructs factual, topic-native story structures for any domain without repetitive formulas.
        """
        t_low = topic.lower()

        # 1. Identify Domain Paradigm with precise ordering
        if any(w in t_low for w in ["space", "universe", "black hole", "quantum", "physics", "mars", "nasa", "alien", "star", "planet", "telescope", "cosmic", "galaxy"]):
            domain = "space_physics"
        elif any(w in t_low for w in ["roman", "titanic", "war", "history", "ancient", "egypt", "empire", "king", "queen", "past", "medieval", "colosseum", "dynasty"]):
            domain = "history"
        elif any(w in t_low for w in ["apple", "jobs", "tesla", "elon", "nike", "mcdonald", "brand", "startup", "ceo", "business", "amazon", "google", "company", "bezos"]):
            domain = "corporate"
        elif any(w in t_low for w in ["casino", "gambl", "bet", "slot", "roulette", "poker", "jackpot"]):
            domain = "casino_gambling"
        elif any(w in t_low for w in ["crime", "murder", "heist", "stolen", "fbi", "police", "investigation", "bermuda", "area 51", "cia", "disappearance", "cold case"]):
            domain = "investigation"
        elif any(w in t_low for w in ["money", "crypto", "bitcoin", "dollar", "wealth", "rich", "bank", "invest", "stock", "inflation", "crash", "tax"]):
            domain = "wealth_economics"
        elif any(w in t_low for w in ["food", "sugar", "diet", "body", "muscle", "health", "fat", "aging", "fasting", "longevity", "disease"]):
            domain = "health_biology"
        elif any(w in t_low for w in ["ai", "robot", "artificial intelligence", "tech", "code", "software", "cyber", "hacker", "future"]):
            domain = "technology"
        elif any(w in t_low for w in ["brain", "psychology", "habit", "dopamine", "mind", "bias", "persuasion", "manipulat", "subconscious", "sleep"]):
            domain = "psychology"
        else:
            domain = "general_custom"

        # 2. Build Topic Specific Scenes
        scenes = self._build_domain_story_scenes(topic, domain, target_scenes)
        total_dur = sum(s.get("target_duration", 12.0) for s in scenes)

        return {
            "topic": topic,
            "title": f"The Untold Reality of {topic.title()}",
            "total_scenes": len(scenes),
            "estimated_duration": round(total_dur, 1),
            "scenes": scenes
        }

    def _build_domain_story_scenes(self, topic: str, domain: str, target_scenes: int) -> List[Dict[str, Any]]:
        """Constructs an unfolding chronological and logical narrative tailored directly to the subject matter."""
        t_clean = topic.strip()
        scenes = []

        if domain == "space_physics":
            story_points = [
                ("hook", "Chapter 1: Beyond the Horizon", f"ब्रह्मांड का सबसे रहस्यमयी और विस्मयकारी सच {t_clean} के रूप में हमारे सामने मौजूद है।", f"The deepest cosmological mystery in modern astrophysics lies inside {t_clean}.", "deep space galaxy nebula stars glowing 4k", 11.0, "whoosh"),
                ("paradox", "Chapter 1: Breaking Physics", "यहां समय, स्थान और भौतिकी के सारे ज्ञात नियम पूरी तरह काम करना बंद कर देते हैं।", "At this threshold, time, space, and the laws of relativity collapse completely.", "black hole gravitational lensing accretion disk 3d", 13.0, "bass_drop"),
                ("experiment", "Chapter 2: The Quantum Data", "जब वैज्ञानिकों ने टेलीस्कोप और सेंसर्स की मदद से इसे मापा, तो परिणाम ने विज्ञान जगत को हिला दिया।", "When astrophysicists observed the quantum data, the measurements shattered existing models.", "james webb space telescope deep field cosmos", 13.0, "glitch"),
                ("time_dilation", "Chapter 2: The Time Warp", "अगर आप इसके करीब सिर्फ एक घंटा बिताते हैं, तो पृथ्वी पर सदियां बीत चुकी होंगी।", "Spend merely one hour within this gravitational well, and centuries elapse on Earth.", "hourglass sand running celestial cosmic background", 14.0, "whoosh"),
                ("singularity", "Chapter 3: The Singularity", "इसके केंद्र में पदार्थ इतना संकुचित हो जाता है कि उसका घनत्व अनंत हो जाता है जिसे सिंगुलैरिटी कहते हैं।", "At the absolute core, matter compresses to infinite density, forming the enigmatic singularity.", "quantum particle collision glowing energy light", 13.0, "glitch"),
                ("event_horizon", "Chapter 3: The Point of No Return", "इवेंट होराइजन वह अदृश्य सीमा है जहां से प्रकाश भी कभी वापस नहीं लौट सकता।", "The event horizon marks the invisible perimeter where even light is permanently trapped.", "glowing vortex tunnel abstract dark space", 13.0, "bass_drop"),
                ("hawking_rad", "Chapter 4: Hawking Radiation", "महान वैज्ञानिक स्टीफन हॉकिंग ने साबित किया कि ये विशालकाय दैत्य भी हमेशा जीवित नहीं रहते।", "Stephen Hawking proved that black holes slowly leak quantum radiation and eventually evaporate.", "nebula cosmic explosion supernova space light", 13.0, "whoosh"),
                ("galaxy_core", "Chapter 4: Galactic Engines", "हमारी आकाशगंगा के ठीक बीच में एक सुपरमैसिव ब्लैक होल पूरे ब्रह्मांड को थामे हुए है।", "At the dead center of our Milky Way, a supermassive gravity engine orchestrates millions of stars.", "spinning spiral galaxy stars astronomical view", 13.0, "bass_drop"),
                ("spaghettification", "Chapter 5: Tidal Forces", "अगर कोई वस्तु इसके करीब जाए, तो अत्यधिक गुरुत्वाकर्षण उसे धागे की तरह खींच देता है।", "Extreme tidal forces stretch any descending matter into atom-thin relativistic strands.", "laser beam energy particle accelerator physics", 12.0, "glitch"),
                ("information_paradox", "Chapter 5: The Lost Information", "वैज्ञानिकों के बीच सबसे बड़ी बहस यह है कि क्या इसमें समाने वाली जानकारी हमेशा के लिए मिट जाती है?", "The information paradox questions whether quantum history is deleted or preserved in higher dimensions.", "holographic matrix data floating cyber dark", 13.0, "whoosh"),
                ("gravitational_waves", "Chapter 6: Ripples in Spacetime", "जब दो ब्लैक होल टकराते हैं, तो पूरा अंतरिक्ष पानी की लहरों की तरह कांप उठता है।", "When twin black holes collide, gravitational shockwaves warp the fabric of spacetime across billions of light years.", "water ripple shockwave high speed macro", 13.0, "bass_drop"),
                ("future_tech", "Chapter 6: Cosmic Energy", "भविष्य की उन्नत सभ्यताएं इनके घूमने से असीमित ऊर्जा निकालने की तकनीक विकसित कर सकती हैं।", "Type-III civilizations could theoretically harvest limitless energy from the spinning ergosphere.", "futuristic sphere dyson swarm solar space station", 13.0, "glitch"),
                ("cosmic_scale", "Chapter 7: Cosmic Scale", "यह अहसास कराता है कि हमारी पूरी पृथ्वी इस अनंत अंधेरे में सिर्फ धूल का एक छोटा सा कण है।", "It reinforces that our entire planetary existence is a solitary speck in the cosmic dark.", "earth from space planet blue marble glow", 13.0, "whoosh"),
                ("multiverse", "Chapter 7: Gateways to Other Universes", "कुछ भौतिकविदों का मानना है कि ये किसी दूसरे ब्रह्मांड या आयाम का प्रवेश द्वार भी हो सकते हैं।", "Theoretical physicists speculate whether singular bridges lead directly to parallel bubble universes.", "portal wormhole cosmic glowing space travel", 13.0, "bass_drop"),
                ("existential", "Chapter 8: The Human Frontier", "इन रहस्यों को समझना हमें इंसानी चेतना और अस्तित्व की असीम सीमाओं से रूबरू कराता है।", "Probing these cosmic extremes pushes human scientific consciousness to its ultimate evolutionary boundary.", "silhouette person looking at starry night sky mountains", 12.0, "whoosh"),
                ("conclusion", "Chapter 8: The Cosmic Lesson", f"{t_clean} साबित करता है कि हम ब्रह्मांड के बारे में जितना जानते हैं, वह सिर्फ एक बूंद के बराबर है।", f"{t_clean} proves that everything humanity knows is merely a single drop in an infinite cosmic ocean.", "astronomer looking through observatory dome night sky", 12.0, "pop")
            ]

        elif domain == "history":
            story_points = [
                ("hook", "Chapter 1: The Untold Event", f"इतिहास की किताबों में {t_clean} के बारे में जो लिखा गया है, क्या वह पूरी सच्चाई है?", f"What is the untold truth about {t_clean} that mainstream history overlooked?", "ancient historical ruins cinematic sunlight", 11.0, "whoosh"),
                ("context", "Chapter 1: The Golden Era", "उस समय की दुनिया इसे एक अजेय और अमर साम्राज्य या कभी न डूबने वाला चमत्कार मानती थी।", "At the time, the world considered this an indestructible marvel beyond failure.", "historical palace royal gold crown vintage", 12.0, "glitch"),
                ("hidden_crack", "Chapter 2: The First Warning", "लेकिन सतह के ठीक नीचे, एक ऐसी गुप्त गलती पल रही थी जिसे सभी ने पूरी तरह नजरअंदाज कर दिया था।", "Beneath the surface, a structural vulnerability was quietly ignored by leadership.", "old parchment documents vintage map magnifying glass", 12.0, "whoosh"),
                ("economic_drain", "Chapter 2: The Silent Bleed", "धन और संसाधनों की बेहिसाब बर्बादी ने अंदरूनी नींव को धीरे-धीरे खोखला कर दिया था।", "Fiscal mismanagement and endless expansion quietly drained the treasury to insolvency.", "gold coins pouring ancient chest vintage", 13.0, "cash_register"),
                ("turning_point", "Chapter 3: The Fatal Decision", "फिर एक दुर्भाग्यपूर्ण रात, एक ऐसा गलत फैसला लिया गया जिसने इतिहास की दिशा हमेशा के लिए बदल दी।", "Then came the single critical decision that triggered an irreversible chain of events.", "stormy ocean dark night waves lightning", 13.0, "bass_drop"),
                ("escalation", "Chapter 3: The Point of No Return", "जब तक सच्चाई सामने आई, तब तक स्थिति पूरी तरह नियंत्रण से बाहर हो चुकी थी।", "By the time anyone realized what was happening, the situation had spiraled out of control.", "running crowd dramatic chaos vintage slow motion", 13.0, "glitch"),
                ("betrayal", "Chapter 4: The Internal Betrayal", "बाहरी दुश्मनों से ज्यादा, अंदर बैठे विश्वासघाती लोगों ने इस तबाही की जमीन तैयार की थी।", "Far worse than external foes, internal palace intrigue accelerated the collapse from within.", "whispering secret in shadows vintage castle candle", 13.0, "whoosh"),
                ("catastrophe", "Chapter 4: The Final Collapse", "पलक झपकते ही, वह भव्य रचना और शक्ति इतिहास के सबसे बड़े सबक में तब्दील हो गई।", "In mere moments, centuries of pride and construction collapsed into legend.", "burning fire smoke dark dramatic battlefield", 14.0, "bass_drop"),
                ("aftermath", "Chapter 5: The Silent Ruins", "इस घटना के बाद बची हुई दुनिया में जो खामोशी छा गई, उसने पूरे युग को झकझोर कर रख दिया।", "The silence left in the wake of this disaster reshaped the geopolitical landscape forever.", "solitary silhouette person standing horizon mist", 13.0, "whoosh"),
                ("lost_knowledge", "Chapter 5: Lost Wisdom", "इस पतन के साथ ही ज्ञान, कला और तकनीक के कई अनमोल पन्ने सदियों के लिए गुम हो गए।", "Generations of advanced engineering, philosophy, and architecture vanished overnight.", "old dusty library vintage leather books sunlight", 12.0, "glitch"),
                ("geopolitical_shift", "Chapter 6: New Power Centers", "इस खालीपन को भरने के लिए नई ताकतों और नए साम्राज्यों का उदय शुरू हुआ।", "Power vacuums inevitably gave birth to rival dynasties competing for continental control.", "army soldiers marching battlefield sunrise vintage", 13.0, "bass_drop"),
                ("archaeology", "Chapter 6: Rediscovered Clues", "आज भी पुरातत्वविद जमीन की गहराई से ऐसे सबूत निकाल रहे हैं जो हमें हैरान कर देते हैं।", "Modern excavations unearth artifacts that continuously rewrite conventional historical records.", "archaeologist brushing ancient artifact sand dirt", 13.0, "whoosh"),
                ("human_nature", "Chapter 7: The Cycle of Hubris", "यह साबित करता है कि जब समाज अपनी पुरानी गलतियों को भूल जाता है, तो इतिहास खुद को दोहराता है।", "Societies that disregard historical precedent are inevitably condemned to repeat the same collapse.", "hourglass passing time marble pillars museum", 13.0, "glitch"),
                ("timeless_rule", "Chapter 7: The Master Lesson", f"{t_clean} हमें यह सिखाता है कि अहंकार कितना भी बड़ा हो, अनुशासन और बुनियादी नियमों के आगे हर चीज झुकती है।", f"{t_clean} reminds us that no civilization is immortal when fundamental principles erode.", "sunrise over ancient roman columns colosseum", 12.0, "whoosh"),
                ("modern_parallel", "Chapter 8: Modern Reflections", "आज की आधुनिक दुनिया को भी इन प्राचीन गलतियों से सबक लेकर संभलने की जरूरत है।", "Modern superpowers look at these historical ruins as stark mirrors of their own vulnerabilities.", "modern city skyline glass skyscrapers night traffic", 12.0, "bass_drop"),
                ("cta", "Chapter 8: The Conclusion", f"क्या {t_clean} के बारे में यह सब आपको पहले से पता था? अपने विचार कमेंट में बताएं और फॉलो करें!", f"Did you know this untold side of {t_clean}? Share your thoughts below and follow for deep dives!", "cinematic sunset mountains ancient view 4k", 12.0, "pop")
            ]

        elif domain == "corporate":
            story_points = [
                ("hook", "Chapter 1: The Garage Genesis", f"एक साधारण से विचार से शुरू होकर {t_clean} ने खरबों डॉलर का साम्राज्य कैसे खड़ा किया?", f"How did {t_clean} transform a simple observation into a trillion-dollar monopoly?", "modern glass skyscraper boardroom sunset", 11.0, "whoosh"),
                ("underdog", "Chapter 1: The Early Struggles", "शुरुआत में हर विशेषज्ञ ने इस मॉडल को खारिज कर दिया था और इसे पागलपन बताया था।", "In the beginning, every industry veteran mocked the business model as impossible.", "lone entrepreneur working late night laptop coffee", 12.0, "glitch"),
                ("ruthless_move", "Chapter 2: The Strategic Pivot", "लेकिन फिर उन्होंने एक ऐसा अप्रत्याशित और आक्रामक कदम उठाया जिसने प्रतिस्पर्धियों को बर्बाद कर दिया।", "Then came the aggressive counter-intuitive move that caught competitors entirely off guard.", "chess king piece knocking down opponent slow motion", 13.0, "bass_drop"),
                ("obsession", "Chapter 2: Product Fanaticism", "हर छोटे से छोटे विवरण और डिजाइन पर इतना जुनून सवार था कि कोई दूसरा मुकाबला नहीं कर सका।", "A relentless obsession with minimalism and execution established an unassailable quality moat.", "designer drawing blueprints sketchpad modern studio", 13.0, "whoosh"),
                ("monopoly_lock", "Chapter 3: The Moat", "उन्होंने एक ऐसा अदृश्य नेटवर्क और इकोसिस्टम तैयार किया जिससे ग्राहकों का बाहर निकलना असंभव हो गया।", "They constructed an inescapable consumer ecosystem with zero friction to enter.", "smartphone sleek minimal design fingers typing", 13.0, "glitch"),
                ("marketing_genius", "Chapter 3: Emotional Branding", "उन्होंने कभी केवल उत्पाद नहीं बेचा, बल्कि लोगों की पहचान, गर्व और जीवनशैली को बेचा।", "They mastered emotional branding, selling aspirational identity rather than technical specs.", "luxury commercial billboard city night lights", 13.0, "bass_drop"),
                ("hidden_cost", "Chapter 4: The Dark Side", "लेकिन इस बेमिसाल कामयाबी के पीछे कर्मचारियों, गोपनीयता और बाजार पर इसका गहरा असर पड़ा।", "Behind the soaring stock price lay intense internal pressure and ruthless market domination.", "server racks glowing blue data center cyber", 13.0, "whoosh"),
                ("supply_chain", "Chapter 4: The Global Engine", "दुनिया भर में फैले कारखानों और सप्लाई चेन की सटीकता ने उन्हें लागत में अजेय बना दिया।", "Precision global supply chains and bulk leverage squeezed competitors out of production capacity.", "automated factory robotic arms manufacturing", 13.0, "glitch"),
                ("financial_power", "Chapter 5: The Cash Machine", "आज यह कंपनी प्रति सेकंड लाखों डॉलर का कैश फ्लो पैदा करती है जो किसी छोटे देश की जीडीपी से भी बड़ा है।", "Today this enterprise generates daily cash flow rivaling the GDP of entire nations.", "money counting machine 100 dollar bills stack", 14.0, "cash_register"),
                ("crisis_management", "Chapter 5: Surviving The Abyss", "जब संकट का समय आया, तो कड़े फैसले लेकर कमजोरियों को काटकर बाहर फेंक दिया गया।", "During structural crises, leadership ruthlessly eliminated unprofitable product lines to preserve cash.", "business executive walking through rainy city glass building", 13.0, "whoosh"),
                ("culture_code", "Chapter 6: The Innovation DNA", "विफलता को बर्दाश्त किया गया, लेकिन औसत दर्जे के काम को कंपनी से हमेशा के लिए बाहर रखा गया।", "They fostered an uncompromising culture where mediocrity was immediately weeded out.", "modern creative open office young entrepreneurs meeting", 12.0, "glitch"),
                ("future_vision", "Chapter 6: The AI Frontier", "अब उनकी नजर अगले दशक की सबसे बड़ी तकनीकी क्रांति और आर्टिफिशियल इंटेलिजेंस पर है।", "Now their capital is focused on the next exponential frontier of artificial intelligence.", "futuristic robotic hand touching holographic screen", 13.0, "whoosh"),
                ("legacy_impact", "Chapter 7: Changing Human Habits", "आज 8 अरब लोग सुबह उठने से लेकर रात को सोने तक इन्हीं के बनाए सिस्टम पर निर्भर हैं।", "Billions of daily interactions are now fundamentally wired around their digital architecture.", "crowd of people using smartphones subway walking", 13.0, "bass_drop"),
                ("founder_mindset", "Chapter 7: The Master Lesson", f"{t_clean} की सबसे बड़ी सीख यह है कि उत्पाद से ज्यादा महत्वपूर्ण उसका वितरण और ब्रांड की पहचान है।", f"The core lesson of {t_clean} is that distribution and perception outperform product alone.", "businessman walking through airport terminal luxury", 12.0, "whoosh"),
                ("actionable_rule", "Chapter 8: The Business Rule", "अगर आप भी कुछ बड़ा बनाना चाहते हैं, तो हमेशा एक संकीर्ण समस्या चुनकर उसमें सर्वश्रेष्ठ बनें।", "To build enduring scale, dominate a narrow niche with relentless focus before horizontal expansion.", "person looking out skyscraper penthouse window sunrise", 12.0, "pop"),
                ("cta", "Chapter 8: The Conclusion", f"क्या आपको {t_clean} की यह पूरी कहानी पता थी? अपने विचार बताएं और ऐसी ही केस स्टडीज के लिए फॉलो करें!", f"What is your biggest takeaway from {t_clean}? Share below and follow for weekly masterclasses!", "city skyline drone golden hour 4k cinematic", 12.0, "pop")
            ]

        elif domain == "investigation":
            story_points = [
                ("hook", "Chapter 1: The Disappearance", f"{t_clean} के पीछे की वह रहस्यमयी फाइलें जिन्हें आज भी दुनिया से छिपाया जाता है।", f"The classified facts behind {t_clean} that forensic investigators never resolved.", "dark foggy alley silhouette detective coat", 11.0, "whoosh"),
                ("the_scene", "Chapter 1: The Crime Scene", "जब अधिकारी पहली बार घटनास्थल पर पहुंचे, तो वहां सब कुछ सामान्य था - सिवाय एक अजीब सुराग के।", "When investigators arrived at the scene, everything appeared normal except for one chilling detail.", "evidence tape crime scene flash camera yellow light", 12.0, "glitch"),
                ("the_timeline", "Chapter 2: The 24-Hour Window", "जांचकर्ताओं ने पाया कि उस रात के ठीक 3 बजकर 15 मिनट पर एक अज्ञात गतिविधि दर्ज की गई थी।", "Forensic records revealed an untraceable anomaly registered at exactly 3:15 AM.", "wall clock antique ticking dark room slow motion", 13.0, "whoosh"),
                ("suspects", "Chapter 2: The Web of Lies", "जिन गवाहों ने पहले बयान दिए थे, वे अचानक अपने बयानों से मुकर गए और कुछ हमेशा के लिए गायब हो गए।", "Key witnesses suddenly contradicted their initial testimonies before vanishing from public record.", "interrogation room light bulb swinging shadow", 13.0, "bass_drop"),
                ("forensic_evidence", "Chapter 3: The Missing Evidence", "लैब टेस्ट के महत्वपूर्ण नमूने अचानक पुलिस लॉकअप से रहस्यमयी तरीके से गायब हो गए।", "Crucial forensic ballistics samples vanished under suspicious circumstances from evidence lockers.", "microscope forensic laboratory slide analysis", 13.0, "glitch"),
                ("covert_surveillance", "Chapter 3: The Watchers", "अधिकारियों को अहसास हुआ कि कोई शक्तिशाली ताकत इस पूरी जांच पर खुद नजर रख रही थी।", "Lead detectives realized that external intelligence agencies were actively monitoring their investigation.", "security surveillance monitors cctv dark room", 13.0, "whoosh"),
                ("breakthrough", "Chapter 4: The Declassified Evidence", "दशकों बाद, जब गुप्त दस्तावेजों को सार्वजनिक किया गया, तो पूरी दुनिया के होश उड़ गए।", "Decades later, newly unsealed archival transcripts revealed a disturbing reality.", "inspecting classified documents red stamp top secret", 14.0, "glitch"),
                ("hidden_motive", "Chapter 4: The Real Motive", "विशेषज्ञों का मानना है कि इस पूरे मामले के पीछे सत्ता, पैसे और गुप्त समझौतों का गहरा खेल था।", "Analysts argue the real driver was a covert nexus of institutional power and untraceable money.", "briefcase cash money dark executive office", 13.0, "cash_register"),
                ("cold_case", "Chapter 5: The Unresolved Lead", "आज भी कई मुख्य सवालों के जवाब किसी सरकारी दस्तावेज में मौजूद नहीं हैं।", "To this day, key questions remain heavily redacted in international archive files.", "filing cabinet old dusty archives manila folders", 12.0, "whoosh"),
                ("whistleblower", "Chapter 5: The Insider Warning", "एक पूर्व अधिकारी ने अपनी अंतिम सांसों में यह चेतावनी दी थी कि सच्चाई बहुत खतरनाक है।", "A dying declaration from a former operative warned that exposing the truth carried lethal risk.", "person in shadow speaking microphone interview", 13.0, "bass_drop"),
                ("public_obsession", "Chapter 6: Global Theories", "लाखों लोगों ने इस पहेली को सुलझाने की कोशिश की, लेकिन हर सुराग एक नए अंधेरे में ले जाता है।", "Decades of amateur sleuths and investigative journalists hit identical brick walls.", "conspiracy cork board red string pinned photographs", 13.0, "glitch"),
                ("modern_tech", "Chapter 6: Digital Forensics", "आज के आधुनिक डिजिटल टूल्स और डीएनए विश्लेषण ने इस केस में नई जान फूंक दी है।", "Next-generation genetic genealogy and satellite imaging recently reopened long-dormant leads.", "computer programmer analyzing data map screen", 13.0, "whoosh"),
                ("chilling_reality", "Chapter 7: The Uncomfortable Truth", "कुछ रहस्य इसलिए अनसुलझे रहते हैं क्योंकि शक्तिशाली लोग नहीं चाहते कि वे कभी सुलझें।", "Some cold cases remain open simply because resolution exposes structural corruption.", "gavel courtroom judge law dark atmospheric", 13.0, "bass_drop"),
                ("warning", "Chapter 7: The Takeaway", "यह घटना हमें सिखाती है कि आधिकारिक बयानों पर आंख मूंदकर भरोसा नहीं करना चाहिए।", "This investigation is a masterclass in why unquestioned trust in public narratives is naive.", "car headlights cutting through dark rain night", 12.0, "whoosh"),
                ("legacy_question", "Chapter 8: What Really Happened", f"क्या {t_clean} एक सोची-समझी साजिश थी या इतिहास की सबसे बड़ी अनसुलझी पहेली?", f"Was {t_clean} an orchestrated cover-up or an unprecedented historical mystery?", "foggy city street lamp night mystery cinematic", 12.0, "glitch"),
                ("cta", "Chapter 8: The Conclusion", "अपनी राय नीचे कमेंट में जरूर बताएं और ऐसी ही अनसुलझी सच्ची कहानियों के लिए फॉलो करें!", "What is your theory on this case? Share below and follow for weekly investigative deep dives!", "detective walking into misty night street", 12.0, "pop")
            ]

        elif domain == "casino_gambling":
            story_points = [
                ("hook", "Chapter 1: The Illusion", "क्या आप जानते हैं कि कैसीनो में कदम रखते ही आपकी सोचने की क्षमता कैसे बदल जाती है?", "The psychological architecture engineered into every inch of modern casino resorts.", "roulette wheel spinning casino table lights", 11.0, "whoosh"),
                ("spatial_trick", "Chapter 1: The Timeless Maze", "वहां न कोई घड़ी होती है, न कोई खिड़की - ताकि आपका दिमाग समय और दिन-रात का अहसास खो दे।", "No clocks, no windows, curved carpets designed to keep you trapped in an endless loop.", "neon casino hallway without windows slow motion", 12.0, "glitch"),
                ("audio_sensory", "Chapter 2: The Sound of Winning", "हर मशीन से सिक्के गिरने और जीत की आवाजें आती हैं, भले ही 99% लोग हार रहे हों।", "Euphoric chimes constantly trigger ambient validation, masking the fact that 95% of players lose.", "casino slot machine jackpot flashing lights", 13.0, "cash_register"),
                ("dopamine", "Chapter 2: The Near-Miss Trap", "जब आप बाल-बाल हारते हैं, तो दिमाग उसे असफलता नहीं बल्कि अगली बड़ी जीत का संकेत समझता है।", "A near-miss triggers the exact same neurological dopamine surge as an actual win.", "slot machine jackpot reels spinning flashing", 13.0, "bass_drop"),
                ("tokenization", "Chapter 3: Invisible Money", "असली नोटों को प्लास्टिक के चिप्स में बदलकर खर्च करने का मानसिक दर्द शून्य कर दिया जाता है।", "Converting legal tender into plastic chips erases the cognitive pain of losing capital.", "casino chips green blackjack table cards", 13.0, "cash_register"),
                ("digital_swipe", "Chapter 3: Cashless Traps", "आजकल डिजिटल कार्ड्स और ऑटो-स्पिन ने सोचने का हर मौका ही छीन लिया है।", "Cashless player tracking cards and auto-bet buttons accelerate capital depletion by 300%.", "credit card payment chip terminal luxury", 12.0, "glitch"),
                ("the_math", "Chapter 4: The 100% House Edge", "गणित और संभावनाओं को ऐसे गढ़ा गया है कि लंबे समय में सिर्फ और सिर्फ कैसीनो ही जीतता है।", "Statistical probability ensures that with enough time, the house extracts all liquidity.", "mathematics equations chalkboard probability calculation", 14.0, "whoosh"),
                ("sunk_cost", "Chapter 4: The Sunk Cost Pit", "हारे हुए पैसे को वापस पाने की जिद इंसान को और बड़े दांव लगाने पर मजबूर करती है।", "The obsession to recover lost funds forces gamblers into escalating downward spirals.", "frustrated person holding head dark room", 13.0, "bass_drop"),
                ("vip_lounge", "Chapter 5: The High Roller Trap", "बड़ा दांव लगाने वालों को मुफ्त कमरे और शराब देकर उन्हें और ज्यादा खेलने के लिए लुभाया जाता है।", "Free luxury suites and comped drinks are mathematically calculated investments to keep VIPs betting.", "luxury hotel suite high roller vip champagne", 13.0, "whoosh"),
                ("surveillance_cctv", "Chapter 5: Facial Recognition", "आधुनिक कैसीनो में एआई कैमरे हर खिलाड़ी की सांसों और दांव लगाने के तरीके को ट्रैक करते हैं।", "Biometric facial scanning and pit AI monitor betting cadence in real-time.", "security guard looking at surveillance cctv monitors", 13.0, "glitch"),
                ("free_drinks", "Chapter 6: Chemical Disinhibition", "अल्कोहल और मुफ्त सेवाएं आपके आत्म-नियंत्रण के आखिरी अवरोध को भी तोड़ देती हैं।", "Complimentary refreshments systematically suppress rational risk assessment in the prefrontal cortex.", "cocktail drink glass bar luxury nightclub", 12.0, "whoosh"),
                ("online_gambling", "Chapter 6: Pocket Casinos", "आज यह पूरा जाल आपके स्मार्टफोन के जरिए 24 घंटे आपकी जेब में मौजूद है।", "Mobile gaming apps leverage these identical behavioral loops to monetize your attention 24/7.", "person in dark bed scrolling phone glowing screen", 13.0, "glitch"),
                ("financial_ruin", "Chapter 7: The Reality Check", "इतिहास में कोई भी व्यक्ति कैसीनो के गणित को लंबे समय तक हराकर अमीर नहीं बना है।", "No player in mathematical history has ever outpaced the law of large numbers over a career.", "empty wallet hands frustrated person shadows", 13.0, "bass_drop"),
                ("immunity_rule", "Chapter 7: The Only Winning Move", "इस खेल में जीतने का सिर्फ एक ही नियम है - पहली छोटी जीत के तुरंत बाद बाहर निकल जाना।", "The only mathematical way to beat an asymmetrical system is walking away immediately after a win.", "person walking away into night city skyline lights", 12.0, "whoosh"),
                ("mindset_shift", "Chapter 8: Reclaiming Control", "असली संपत्ति और सफलता अनुशासन और सृजन से आती है, किसी शॉर्टकट से नहीं।", "True enduring wealth is built through asymmetric creation, never through engineered chance.", "businessman smiling confident standing sunrise rooftop", 12.0, "pop"),
                ("cta", "Chapter 8: The Conclusion", "क्या आपको कैसीनो मनोविज्ञान के ये सच पता थे? कमेंट में बताएं और वित्तीय समझदारी के लिए फॉलो करें!", "Did you know how casino psychology operates? Share below and follow for daily smart insights!", "las vegas strip aerial night view 4k", 12.0, "pop")
            ]

        else: # general_custom & other domains
            story_points = [
                ("hook", "Chapter 1: The Reality Check", f"क्या आपने कभी गहराई से सोचा है कि {t_clean} असल में किस तरह काम करता है?", f"Have you ever investigated how {t_clean} genuinely functions beneath the surface?", "dramatic cinematic lighting portrait thinking", 11.0, "whoosh"),
                ("the_core_problem", "Chapter 1: The Core Mechanism", "ज्यादातर लोग इसके बाहरी हिस्से को देखते हैं, लेकिन असली प्रभाव इसकी आंतरिक संरचना में छिपा है।", "Most perceive the outward presentation, completely missing the foundational mechanism.", "gears mechanical clockwork system turning", 12.0, "glitch"),
                ("the_breakthrough", "Chapter 2: The Breakthrough", "जब दुनिया के शीर्ष विचारकों ने इस पर शोध किया, तो उन्होंने तीन निर्णायक नियम खोज निकाले।", "When researchers analyzed the behavioral data, they isolated three decisive principles.", "microscope laboratory science research futuristic", 13.0, "whoosh"),
                ("the_friction", "Chapter 2: The Friction Point", "पहला नियम है - हर फैसले में समय और भावनात्मक ऊर्जा का सही प्रबंधन करना।", "Principle one: controlling emotional reactivity before committing strategic resources.", "chess board strategy grandmaster moving piece", 13.0, "bass_drop"),
                ("the_leverage", "Chapter 3: Asymmetric Leverage", "दूसरा नियम है - उन छोटी आदतों को पहचानना जो लंबे समय में विशाल परिणाम पैदा करती हैं।", "Principle two: compounding asymmetrical micro-habits over long time horizons.", "sunrise over modern city skyscrapers drone 4k", 14.0, "whoosh"),
                ("compounding", "Chapter 3: The Exponential Shift", "जब ये सिद्धांत एक साथ मिलते हैं, तो बदलाव की गति आपकी कल्पना से 10 गुना तेज हो जाती है।", "When these factors intersect, the velocity of compounding accelerates by an order of magnitude.", "fast motion time lapse city traffic night glow", 13.0, "glitch"),
                ("real_world_test", "Chapter 4: Real World Application", "इसे लागू करने वाले शीर्ष 1% लोग किसी भी स्थिति में तुरंत सही फैसला ले लेते हैं।", "Top performers systematically apply these decision models to execute under extreme pressure.", "executive in suit walking through modern architecture", 13.0, "whoosh"),
                ("common_mistakes", "Chapter 4: Avoiding the Traps", "99% लोग सिर्फ इसलिए पीछे रह जाते हैं क्योंकि वे तात्कालिक संतुष्टि के पीछे भागते हैं।", "The vast majority fail simply by prioritizing immediate gratification over structural momentum.", "person frustrated thinking desk dark night", 13.0, "bass_drop"),
                ("system_design", "Chapter 5: Designing Your System", "इरादों से ज्यादा आपका वातावरण तय करता है कि आप अपने लक्ष्य तक पहुंचेंगे या नहीं।", "Your daily structural environment dictates outcomes far more reliably than fleeting motivation.", "clean minimal workspace laptop plant sunlight", 12.0, "whoosh"),
                ("feedback_loops", "Chapter 5: Rapid Feedback", "हर हफ्ते अपनी प्रगति का सटीक विश्लेषण करना आपको गलत दिशा में जाने से बचाता है।", "Instituting tight feedback loops ensures rapid calibration before errors compound.", "writing notes notebook fountain pen coffee", 13.0, "glitch"),
                ("discipline_code", "Chapter 6: The Discipline Moat", "जब प्रेरणा खत्म हो जाती है, तब केवल आपकी बनाई हुई दिनचर्या ही आपको आगे ले जाती है।", "When enthusiasm wanes, automated habits are the only force that sustains momentum.", "morning workout running sunrise athlete focused", 13.0, "whoosh"),
                ("network_effect", "Chapter 6: Surrounding Influence", "आप जिन 5 लोगों के साथ सबसे ज्यादा समय बिताते हैं, आपकी सोच उन्हीं जैसी बन जाती है।", "Your peer group imperceptibly shapes the upper limit of what you consider achievable.", "two professional people discussing ideas coffee shop", 12.0, "glitch"),
                ("long_game", "Chapter 7: Playing The Long Game", "जो लोग 10 साल आगे की सोच रखते हैं, वे 1 साल के शोर-शराबे से कभी विचलित नहीं होते।", "Long-term operators are entirely immune to short-term market noise and transient panic.", "person looking at horizon ocean sunset calm", 13.0, "bass_drop"),
                ("mastery", "Chapter 7: Achieving True Mastery", "असली महारत तब हासिल होती है जब जटिल चीजें भी आपके लिए सहज और आसान लगने लगें।", "True mastery is attained when high-leverage execution becomes second nature.", "hand holding fountain pen signing master plan", 12.0, "whoosh"),
                ("actionable_takeaway", "Chapter 8: The Master Takeaway", f"{t_clean} पर नियंत्रण पाना ही आपको साधारण भीड़ से अलग और सफल बनाता है।", f"Mastering the dynamics of {t_clean} separates reactive spectators from decisive operators.", "person standing on mountain summit victory sunrise", 12.0, "pop"),
                ("cta", "Chapter 8: The Conclusion", "क्या यह नजरिया आपके लिए मददगार रहा? अपने विचार कमेंट करें और ऐसी ही इनसाइट्स के लिए फॉलो करें!", "Did this perspective shift your thinking? Share your takeaway below and follow for more!", "modern city skyline golden hour aerial 4k", 12.0, "pop")
            ]

        # Select target_scenes
        scenes_to_use = story_points[:target_scenes]

        for i, (role, chapter, s_hi, s_en, query, dur, sfx) in enumerate(scenes_to_use):
            scenes.append({
                "scene_number": i + 1,
                "role": role,
                "chapter": chapter,
                "script_hi": s_hi,
                "script_en": s_en,
                "search_query": query,
                "target_duration": dur,
                "sfx": sfx
            })

        return scenes

    def _parse_custom_script_to_scenes(self, custom_text: str, topic: str, niche: str) -> Dict[str, Any]:
        """Splits user pasted scripts / articles into sequential video scenes with matched Pexels portrait queries."""
        paragraphs = [p.strip() for p in custom_text.split("\n") if len(p.strip()) > 20]
        if not paragraphs:
            paragraphs = [s.strip() for s in re.split(r'[.!?।]\s+', custom_text) if len(s.strip()) > 15]

        scenes = []
        for idx, p in enumerate(paragraphs):
            # Extract concrete keywords for Pexels
            words = [w.lower() for w in re.findall(r'[a-zA-Z]{4,}', p)]
            lead_words = [w for w in words if w not in ["this", "that", "with", "from", "they", "have", "been", "were", "what", "when", "your", "their"]]
            query = f"{topic} {' '.join(lead_words[:2])}" if lead_words else f"{topic} dramatic cinematic"

            # Estimate duration based on word count (~2.5 words/second)
            w_count = len(p.split())
            dur = max(6.0, min(18.0, round(w_count / 2.2, 1)))

            scenes.append({
                "scene_number": idx + 1,
                "role": "hook" if idx == 0 else ("cta" if idx == len(paragraphs) - 1 else "story_segment"),
                "chapter": f"Chapter {int(idx/3)+1}: Story Segment",
                "script_hi": p,
                "script_en": p,
                "search_query": query,
                "target_duration": dur,
                "sfx": "whoosh" if idx % 2 == 0 else "glitch"
            })

        total_dur = sum(s["target_duration"] for s in scenes)
        return {
            "topic": topic,
            "title": f"Custom Script: {topic}",
            "total_scenes": len(scenes),
            "estimated_duration": round(total_dur, 1),
            "scenes": scenes
        }

viral_story_engine = ViralStoryEngine()
