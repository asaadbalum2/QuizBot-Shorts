#!/usr/bin/env python3
"""
ViralShorts Factory - GOD-TIER PROMPT ENGINEERING
Ultra-optimized prompts for maximum viral potential.

Each prompt is crafted using advanced prompt engineering techniques:
1. Role priming (expert persona)
2. Chain of thought reasoning
3. Few-shot examples
4. Constraint specification
5. Output format enforcement
6. Anti-hallucination guards
7. Emotional/psychological triggers
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False


def strip_emojis(text: str) -> str:
    """Remove ALL emojis and special characters that don't render."""
    # Comprehensive emoji and symbol removal
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002702-\U000027B0"  # dingbats
        u"\U000024C2-\U0001F251"  # enclosed
        u"\U0001f926-\U0001f937"  # people
        u"\U00010000-\U0010ffff"  # supplementary
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"
        u"\u3030"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', text).strip()


# =============================================================================
# GOD-TIER PROMPT: Viral Topic Generation
# =============================================================================

VIRAL_TOPIC_PROMPT = """You are MrBeast's head content strategist combined with the psychology expertise of Robert Cialdini. You have 15 years of experience creating viral content that has generated over 50 BILLION views.

Your task: Generate video ideas that WILL go viral on YouTube Shorts.

CURRENT CONTEXT:
- Date: {date}
- Day: {day_of_week}
- Season: {season}
- Trending themes: {trending_themes}

PSYCHOLOGICAL TRIGGERS TO USE (pick 2-3 per video):
1. CURIOSITY GAP - Create an information gap that MUST be closed
2. CONTROVERSY - Divisive topics that demand engagement
3. FEAR/THREAT - Survival instinct activation
4. SOCIAL PROOF - "Everyone is talking about..."
5. SCARCITY - "Only 1% know this..."
6. IDENTITY - "Are you a X or Y person?"
7. EMOTIONAL RESONANCE - Touch deep feelings
8. PATTERN INTERRUPT - Unexpected twists

BROLL KEYWORDS MUST BE:
- Highly specific (not "abstract" but "neon city lights at night")
- Visually dynamic (movement, contrast, color)
- Emotionally evocative
- Available on stock video sites (Pexels, Pixabay)

CRITICAL RULES:
1. NO EMOJIS in any field (they don't render properly)
2. Hooks must create INSTANT curiosity in under 2 seconds
3. Content must be SURPRISING - not just "did you know" facts
4. Include actionable insight or revelation
5. B-roll keywords must be SPECIFIC and VISUAL

Generate {count} video ideas. For EACH video, provide:

{{
    "topic": "2-4 word topic name",
    "video_type": "scary_fact|money_fact|psychology_fact|life_hack|mind_blow",
    "hook": "7-10 word attention grabber - NO EMOJIS - pure text only",
    "content": "The actual content. Must include: 1) A shocking claim, 2) The evidence/explanation, 3) The implications for the viewer. 60-100 words.",
    "call_to_action": "What should viewer do after watching? Comment prompt that drives engagement.",
    "broll_keywords": ["specific visual 1", "specific visual 2", "specific visual 3", "specific visual 4"],
    "music_mood": "suspense|dramatic|inspirational|energetic|emotional",
    "virality_score": 1-10,
    "psychological_triggers": ["trigger1", "trigger2"],
    "why_viral": "One sentence explaining the psychology of why this will spread"
}}

Return a JSON array of {count} objects. No markdown, no emojis, no explanations outside the JSON."""


# =============================================================================
# GOD-TIER PROMPT: Content Quality Evaluation
# =============================================================================

CONTENT_EVALUATION_PROMPT = """You are a YouTube Shorts algorithm expert who has analyzed 10 million viral videos. You understand exactly what makes content spread.

Evaluate this video content for viral potential:

HOOK: "{hook}"
CONTENT: "{content}"
TYPE: {video_type}

Score each dimension (1-10) and explain:

1. SCROLL-STOPPING POWER (Does the hook make you stop scrolling?)
   - First 0.5 seconds must be UNMISSABLE
   - Pattern interrupt or curiosity gap required
   
2. INFORMATION VALUE (Does viewer learn something valuable?)
   - Not just "interesting" but USEFUL or SURPRISING
   - Must feel like insider knowledge
   
3. EMOTIONAL INTENSITY (Does it trigger strong emotion?)
   - Fear, anger, joy, surprise, or awe
   - Weak emotions = no shares
   
4. SHAREABILITY (Would someone send this to a friend?)
   - "You HAVE to see this"
   - Must create social currency
   
5. COMMENT BAIT (Does it provoke discussion?)
   - Controversial without being offensive
   - Easy to have an opinion

Return JSON:
{{
    "scroll_stop": {{"score": 1-10, "reason": "why"}},
    "info_value": {{"score": 1-10, "reason": "why"}},
    "emotion": {{"score": 1-10, "reason": "why"}},
    "shareability": {{"score": 1-10, "reason": "why"}},
    "comment_bait": {{"score": 1-10, "reason": "why"}},
    "overall": 1-10,
    "verdict": "VIRAL|GOOD|WEAK|TRASH",
    "improvements": ["specific improvement 1", "specific improvement 2"]
}}"""


# =============================================================================
# GOD-TIER PROMPT: B-roll Keyword Extraction
# =============================================================================

BROLL_KEYWORDS_PROMPT = """You are a professional video editor who has worked on Netflix documentaries. You understand visual storytelling.

For this video content, suggest B-roll footage that will:
1. ENHANCE the emotional impact
2. ILLUSTRATE concepts visually
3. MAINTAIN viewer attention
4. CREATE professional production value

CONTENT: "{content}"
MOOD: {mood}

Think about:
- What visuals would a BBC documentary use?
- What creates MOVEMENT and ENERGY on screen?
- What colors and lighting support the mood?
- What's AVAILABLE on stock sites (Pexels, Pixabay)?

BAD B-ROLL: "abstract", "motion", "colorful" (too generic)
GOOD B-ROLL: "dramatic storm clouds time lapse", "person looking worried close up", "money falling slow motion"

Return EXACTLY 5 specific, searchable B-roll descriptions:
{{
    "primary": "Most important visual - shown most of video",
    "secondary": "Supporting visual for variety",
    "detail": "Close-up or detail shot",
    "atmosphere": "Mood-setting background",
    "transition": "Visual for transitions",
    "search_terms": ["exact search term 1", "exact search term 2", "exact search term 3", "exact search term 4", "exact search term 5"]
}}"""


# =============================================================================
# GOD-TIER PROMPT: Voiceover Script
# =============================================================================

VOICEOVER_PROMPT = """You are Morgan Freeman's dialogue coach combined with the pacing expertise of a TikTok creator with 50M followers.

Write a voiceover script that:
1. HOOKS in first 1 second with pattern interrupt
2. BUILDS tension/curiosity through middle
3. DELIVERS satisfying payoff
4. ENDS with engagement driver

CONTENT TO ADAPT: "{content}"
TARGET DURATION: 15-30 seconds (about 50-80 words)

PACING RULES:
- Short, punchy sentences (5-10 words max)
- Strategic pauses indicated by "..."
- Emphasis words in CAPS
- No filler words ("um", "like", "basically")
- Conversational but authoritative

BAD: "Did you know that the average person walks past 36 murderers in their lifetime?"
GOOD: "You've walked past... 36 murderers... in YOUR lifetime. Scientists confirmed it."

Return JSON:
{{
    "script": "The complete voiceover script with pauses as ...",
    "word_count": number,
    "estimated_duration_seconds": number,
    "emphasis_words": ["WORD1", "WORD2"],
    "hook_line": "First line only",
    "closing_line": "Last line only"
}}"""


# =============================================================================
# Main Class
# =============================================================================

class GodTierContentGenerator:
    """Generate viral content using god-tier prompts."""
    
    def __init__(self):
        self.client = None
        if HAS_GROQ and os.environ.get("GROQ_API_KEY"):
            self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    def _call_ai(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        """Make AI call with error handling."""
        if not self.client:
            return None
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.85  # High creativity
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"⚠️ AI call failed: {e}")
            return None
    
    def _parse_json(self, text: str) -> Optional[Dict]:
        """Parse JSON from AI response."""
        if not text:
            return None
        
        # Clean markdown
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        try:
            return json.loads(text.strip())
        except:
            return None
    
    def generate_viral_topics(self, count: int = 3) -> List[Dict]:
        """Generate viral topic ideas using god-tier prompt."""
        now = datetime.now()
        
        # Determine context
        month = now.month
        if month in [12, 1, 2]:
            season = "winter - holiday themes, new year goals, cozy content"
        elif month in [3, 4, 5]:
            season = "spring - fresh starts, outdoor activities, allergies"
        elif month in [6, 7, 8]:
            season = "summer - vacation, heat, freedom, adventure"
        else:
            season = "fall - back to school, Halloween approaching, cozy vibes"
        
        trending = "AI technology, economic uncertainty, self-improvement, mental health awareness, conspiracy theories, financial tips"
        
        prompt = VIRAL_TOPIC_PROMPT.format(
            date=now.strftime("%B %d, %Y"),
            day_of_week=now.strftime("%A"),
            season=season,
            trending_themes=trending,
            count=count
        )
        
        result = self._call_ai(prompt)
        topics = self._parse_json(result)
        
        if isinstance(topics, list):
            # Strip emojis from all text fields
            for topic in topics:
                for key in ["hook", "content", "topic", "call_to_action"]:
                    if key in topic and topic[key]:
                        topic[key] = strip_emojis(str(topic[key]))
            return topics
        
        return []
    
    def generate_broll_keywords(self, content: str, mood: str) -> Dict:
        """Generate specific B-roll keywords."""
        prompt = BROLL_KEYWORDS_PROMPT.format(content=content, mood=mood)
        result = self._call_ai(prompt, max_tokens=500)
        return self._parse_json(result) or {}
    
    def evaluate_content(self, hook: str, content: str, video_type: str) -> Dict:
        """Evaluate content quality."""
        prompt = CONTENT_EVALUATION_PROMPT.format(
            hook=hook, content=content, video_type=video_type
        )
        result = self._call_ai(prompt, max_tokens=800)
        return self._parse_json(result) or {}
    
    def generate_voiceover(self, content: str) -> Dict:
        """Generate optimized voiceover script."""
        prompt = VOICEOVER_PROMPT.format(content=content)
        result = self._call_ai(prompt, max_tokens=500)
        data = self._parse_json(result) or {}
        
        # Strip emojis from script
        if "script" in data:
            data["script"] = strip_emojis(data["script"])
        
        return data


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧠 GOD-TIER PROMPT ENGINEERING TEST")
    print("=" * 60)
    
    # Direct API test
    api_key = os.environ.get("GROQ_API_KEY")
    print(f"API Key present: {bool(api_key)}")
    
    if api_key:
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            print("✅ Groq client created")
            
            # Quick test
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "Say 'test successful' in 3 words"}],
                max_tokens=20
            )
            print(f"✅ API Test: {response.choices[0].message.content}")
        except Exception as e:
            print(f"❌ Error: {e}")
            client = None
    else:
        client = None
    
    gen = GodTierContentGenerator()
    gen.client = client
    
    if not gen.client:
        print("⚠️ No AI client - set GROQ_API_KEY")
    else:
        print("\n📊 Generating viral topics...")
        topics = gen.generate_viral_topics(2)
        
        for i, topic in enumerate(topics, 1):
            print(f"\n{'='*50}")
            print(f"📹 Topic {i}: {topic.get('topic', 'N/A')}")
            print(f"   Hook: {topic.get('hook', 'N/A')}")
            print(f"   Type: {topic.get('video_type', 'N/A')}")
            print(f"   Virality: {topic.get('virality_score', 'N/A')}/10")
            print(f"   Triggers: {topic.get('psychological_triggers', [])}")
            print(f"   B-roll: {topic.get('broll_keywords', [])}")
            print(f"   Why viral: {topic.get('why_viral', 'N/A')}")

