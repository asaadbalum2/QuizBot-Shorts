#!/usr/bin/env python3
"""
ViralShorts Factory - Dynamic Video Generator
Creates videos with DYNAMIC B-roll changes per phrase.

Instead of:
  [Single B-roll for entire video]
  "Your brain is lying to you. Studies show 92% of people give up..."

We do:
  [B-roll: brain scan] "Your brain is lying to you..."
  [B-roll: crowd of people] "Studies show 92% of people..."
  [B-roll: person giving up] "...give up on their goals..."
  [B-roll: success imagery] "But successful people have systems..."

This makes videos WAY more engaging!
"""

import os
import sys
import re
import asyncio
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# MoviePy imports
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips, ImageClip, CompositeAudioClip
)
import moviepy.video.fx.all as vfx

from PIL import Image, ImageDraw, ImageFont

# Our imports
try:
    from script_v2 import (
        generate_voiceover_v2, create_gradient_background,
        download_pexels_video, VIDEO_WIDTH, VIDEO_HEIGHT,
        THEMES, BROLL_DIR, pil_to_moviepy_clip
    )
    from god_tier_prompts import GodTierContentGenerator, strip_emojis
    from background_music import get_background_music
    HAS_DEPS = True
except ImportError as e:
    print(f"⚠️ Missing dependency: {e}")
    HAS_DEPS = False

OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
BROLL_DIR = Path("./assets/broll")
BROLL_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class PhraseSegment:
    """A segment of the video with its own B-roll."""
    text: str
    duration: float  # seconds
    broll_keyword: str
    broll_clip: Optional[str] = None


class DynamicVideoGenerator:
    """Generate videos with per-phrase B-roll changes."""
    
    def __init__(self):
        self.pexels_key = os.environ.get("PEXELS_API_KEY")
        self.groq_key = os.environ.get("GROQ_API_KEY")
    
    def split_into_phrases(self, content: str, target_phrases: int = 4) -> List[str]:
        """
        Split content into natural phrases.
        
        Example:
        Input: "Your brain is lying to you. Studies show 92% of people give up."
        Output: ["Your brain is lying to you", "Studies show 92% of people give up"]
        """
        # Split on periods, commas, and other natural breaks
        # First by sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        phrases = []
        for sentence in sentences:
            # If sentence is long, split on commas
            if len(sentence) > 60:
                parts = sentence.split(',')
                phrases.extend([p.strip() for p in parts if p.strip()])
            else:
                phrases.append(sentence)
        
        # Merge very short phrases
        merged = []
        buffer = ""
        for phrase in phrases:
            if len(buffer) + len(phrase) < 40:
                buffer += " " + phrase if buffer else phrase
            else:
                if buffer:
                    merged.append(buffer)
                buffer = phrase
        if buffer:
            merged.append(buffer)
        
        return merged[:target_phrases]  # Limit to target
    
    def generate_broll_keywords_for_phrases(self, phrases: List[str]) -> List[str]:
        """Use AI to generate specific B-roll keywords for each phrase."""
        if not self.groq_key:
            # Fallback to generic keywords
            defaults = ["dark cityscape", "thinking person", "abstract motion", "success celebration"]
            return defaults[:len(phrases)]
        
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_key)
            
            phrases_text = "\n".join([f"{i+1}. {p}" for i, p in enumerate(phrases)])
            
            prompt = f"""You are a video editor. For each phrase, suggest ONE specific B-roll video keyword.

Phrases:
{phrases_text}

Rules:
- Keywords must be SPECIFIC and searchable (e.g., "person looking at phone" not "technology")
- Match the EMOTIONAL content of each phrase
- Think about what visual would ENHANCE understanding

Return ONLY a JSON array of keywords, one per phrase:
["keyword1", "keyword2", ...]"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )
            
            import json
            result = response.choices[0].message.content
            if "```" in result:
                result = result.split("```")[1].split("```")[0]
                if result.startswith("json"):
                    result = result[4:]
            
            keywords = json.loads(result.strip())
            return keywords
            
        except Exception as e:
            print(f"⚠️ AI keyword generation failed: {e}")
            return ["dramatic scene"] * len(phrases)
    
    def download_broll_for_phrase(self, keyword: str, index: int) -> Optional[str]:
        """Download B-roll for a specific phrase."""
        if not self.pexels_key:
            return None
        
        cache_file = BROLL_DIR / f"phrase_{keyword.replace(' ', '_')}_{index}.mp4"
        
        if cache_file.exists():
            return str(cache_file)
        
        if download_pexels_video(keyword, str(cache_file)):
            return str(cache_file)
        
        return None
    
    async def create_phrase_video_segment(self, phrase: str, broll_path: str,
                                          duration: float, theme) -> CompositeVideoClip:
        """Create a video segment for one phrase."""
        # Load or create background
        if broll_path and os.path.exists(broll_path):
            bg = VideoFileClip(broll_path)
            bg = bg.resize((VIDEO_WIDTH, VIDEO_HEIGHT))
            if bg.duration < duration:
                bg = bg.loop(duration=duration)
            bg = bg.subclip(0, duration)
            bg = bg.fx(vfx.colorx, 0.5)  # Darken
        else:
            # Fallback gradient
            gradient = create_gradient_background(VIDEO_WIDTH, VIDEO_HEIGHT, theme.background_gradient)
            bg = pil_to_moviepy_clip(gradient, duration)
        
        # Create text overlay
        text_img = self.create_phrase_overlay(phrase, VIDEO_WIDTH, VIDEO_HEIGHT // 2, theme)
        text_clip = pil_to_moviepy_clip(text_img, duration)
        text_clip = text_clip.set_position(('center', 'center'))
        
        # Compose
        segment = CompositeVideoClip([bg, text_clip], size=(VIDEO_WIDTH, VIDEO_HEIGHT))
        segment = segment.set_duration(duration)
        
        return segment
    
    def create_phrase_overlay(self, phrase: str, width: int, height: int, theme) -> Image.Image:
        """Create text overlay for a phrase."""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Load font
        font_candidates = [
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        font_path = next((f for f in font_candidates if os.path.exists(f)), None)
        
        try:
            font = ImageFont.truetype(font_path, 52) if font_path else ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Strip emojis
        phrase = strip_emojis(phrase)
        
        # Word wrap
        words = phrase.split()
        lines = []
        current = []
        max_width = width - 80
        
        for word in words:
            current.append(word)
            test = " ".join(current)
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > max_width:
                current.pop()
                if current:
                    lines.append(" ".join(current))
                current = [word]
        if current:
            lines.append(" ".join(current))
        
        # Draw centered with glow
        y = (height - len(lines) * 70) // 2
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            x = (width - (bbox[2] - bbox[0])) // 2
            
            # Glow
            for offset in [3, 2]:
                glow_alpha = 50 + (3 - offset) * 30
                draw.text((x + offset, y + offset), line, fill=(0, 0, 0, glow_alpha), font=font)
                draw.text((x - offset, y - offset), line, fill=(0, 0, 0, glow_alpha), font=font)
            
            # Shadow
            draw.text((x + 2, y + 2), line, fill=(0, 0, 0, 180), font=font)
            
            # Main text
            draw.text((x, y), line, fill=(255, 255, 255, 255), font=font)
            
            y += 70
        
        return img
    
    async def generate_dynamic_video(self, topic: Dict, output_path: str) -> bool:
        """
        Generate a video with dynamic per-phrase B-roll.
        
        This is the MAIN function that creates engaging videos.
        """
        print(f"\n🎬 Generating DYNAMIC video: {topic.get('topic', 'Unknown')}")
        
        hook = strip_emojis(topic.get("hook", ""))
        content = strip_emojis(topic.get("content", ""))
        full_content = f"{hook} {content}"
        
        # Step 1: Split into phrases
        phrases = self.split_into_phrases(full_content, target_phrases=4)
        print(f"   📝 Split into {len(phrases)} phrases")
        
        # Step 2: Generate B-roll keywords for each phrase
        broll_keywords = self.generate_broll_keywords_for_phrases(phrases)
        print(f"   🎬 B-roll keywords: {broll_keywords}")
        
        # Step 3: Download B-roll for each phrase
        broll_clips = []
        for i, keyword in enumerate(broll_keywords):
            clip_path = self.download_broll_for_phrase(keyword, i)
            broll_clips.append(clip_path)
            if clip_path:
                print(f"   ✅ Downloaded B-roll for phrase {i+1}: {keyword}")
        
        # Step 4: Generate voiceover
        voiceover_path = OUTPUT_DIR / "temp_dynamic_vo.mp3"
        duration = await generate_voiceover_v2(full_content, str(voiceover_path))
        print(f"   🎙️ Voiceover: {duration:.1f}s")
        
        # Step 5: Calculate duration per phrase
        phrase_durations = []
        total_chars = sum(len(p) for p in phrases)
        for phrase in phrases:
            phrase_duration = (len(phrase) / total_chars) * duration
            phrase_durations.append(max(phrase_duration, 2.0))  # Min 2s per phrase
        
        # Step 6: Create segments
        theme = random.choice(list(THEMES.values()))
        segments = []
        
        for i, (phrase, broll_path, phrase_duration) in enumerate(zip(phrases, broll_clips, phrase_durations)):
            print(f"   🎞️ Creating segment {i+1}/{len(phrases)}: {phrase[:30]}...")
            segment = await self.create_phrase_video_segment(phrase, broll_path, phrase_duration, theme)
            segments.append(segment)
        
        # Step 7: Concatenate with smooth transitions
        print("   🔗 Concatenating segments with transitions...")
        final_video = concatenate_videoclips(segments, method="compose")
        
        # Step 8: Add voiceover
        vo_clip = AudioFileClip(str(voiceover_path))
        
        # Step 9: Add background music
        music_clip = None
        music_mood = topic.get("music_mood", "dramatic")
        music_path = get_background_music(music_mood)
        if music_path and os.path.exists(music_path):
            try:
                music_clip = AudioFileClip(music_path)
                music_clip = music_clip.volumex(0.12)  # Lower volume for dynamic videos
            except:
                pass
        
        # Mix audio
        if music_clip:
            if music_clip.duration < final_video.duration:
                music_clip = music_clip.loop(duration=final_video.duration)
            music_clip = music_clip.subclip(0, final_video.duration)
            final_audio = CompositeAudioClip([vo_clip, music_clip])
        else:
            final_audio = vo_clip
        
        final_video = final_video.set_audio(final_audio)
        
        # Step 10: Render
        print("   🎥 Rendering final video...")
        final_video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            preset='ultrafast',
            threads=4
        )
        
        print(f"   ✅ Created: {output_path}")
        return True


async def generate_dynamic_viral_video(count: int = 1):
    """Generate dynamic viral videos with per-phrase B-roll."""
    
    print("=" * 60)
    print("🎬 DYNAMIC Video Generator - Per-Phrase B-roll")
    print("=" * 60)
    
    # Get viral topics from god-tier prompts
    from god_tier_prompts import GodTierContentGenerator
    from groq import Groq
    
    gen = GodTierContentGenerator()
    gen.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    topics = gen.generate_viral_topics(count)
    
    video_gen = DynamicVideoGenerator()
    generated = 0
    
    for i, topic in enumerate(topics, 1):
        print(f"\n📹 Video {i}/{count}")
        print(f"   🎯 Topic: {topic.get('topic', 'N/A')}")
        
        output_path = str(OUTPUT_DIR / f"dynamic_{topic.get('video_type', 'fact')}_{random.randint(1000, 9999)}.mp4")
        
        success = await video_gen.generate_dynamic_video(topic, output_path)
        if success:
            generated += 1
    
    print(f"\n{'='*60}")
    print(f"✅ Generated {generated}/{count} dynamic videos")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(generate_dynamic_viral_video(1))

