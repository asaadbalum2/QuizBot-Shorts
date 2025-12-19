#!/usr/bin/env python3
"""
ViralShorts Factory - Multi-Type Video Generator
Generates various types of viral content videos.

Usage:
    python generate_multi.py --type scary_facts --count 1
    python generate_multi.py --type money_facts --count 2
    python generate_multi.py --type ai_quotes --count 1
    python generate_multi.py --type kids --count 1
    python generate_multi.py --type random --count 3  # Mix of types
"""

import os
import sys
import asyncio
import argparse
import random
from pathlib import Path
from typing import Dict, List, Optional

# Import our modules
from video_types import (
    VideoType, VideoContent, MultiTypeContentGenerator,
    get_weighted_random_type, VIDEO_TYPE_WEIGHTS
)

# Import core generation components from script_v2
try:
    from script_v2 import (
        generate_voiceover_v2, create_gradient_background,
        create_option_panel_image, create_vs_badge, create_cta_text,
        create_percentage_reveal_frame, pil_to_moviepy_clip,
        get_multiple_broll_clips, VIDEO_WIDTH, VIDEO_HEIGHT,
        THEMES, VideoTheme
    )
    HAS_V2 = True
except ImportError as e:
    print(f"⚠️ Could not import script_v2: {e}")
    HAS_V2 = False

from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips, ColorClip, CompositeAudioClip
)
import moviepy.video.fx.all as vfx

from PIL import Image, ImageDraw, ImageFont


# Output directory
OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Type-Specific Generators
# =============================================================================

async def generate_fact_video(content: VideoContent, output_path: str) -> bool:
    """Generate a fact-based video (scary facts, money facts)."""
    print(f"\n🎬 Generating {content.video_type.value} video...")
    print(f"   Hook: {content.hook}")
    print(f"   Fact: {content.main_text[:50]}...")
    
    try:
        # THEMES is a dict, get values list
        themes_list = list(THEMES.values())
        
        # Pick theme based on type
        if content.video_type == VideoType.SCARY_FACTS:
            theme = next((t for t in themes_list if "night" in t.name.lower()), random.choice(themes_list))
        elif content.video_type == VideoType.MONEY_FACTS:
            theme = next((t for t in themes_list if "gold" in t.name.lower() or "sunset" in t.name.lower()), random.choice(themes_list))
        else:
            theme = random.choice(themes_list)
        
        print(f"   🎨 Theme: {theme.name}")
        
        # Generate voiceover
        voiceover_path = OUTPUT_DIR / "temp_vo.mp3"
        duration = await generate_voiceover_v2(content.voiceover_script, str(voiceover_path))
        
        # Calculate timing
        total_duration = max(duration + 5, 15)  # At least 15 seconds
        
        # Get B-roll
        broll_clips = get_multiple_broll_clips(
            {"option_a": content.main_text, "option_b": ""},
            count=3
        )
        
        # Create background
        if broll_clips:
            processed = []
            for clip_path in broll_clips[:3]:
                if os.path.exists(clip_path):
                    clip = VideoFileClip(clip_path)
                    clip = clip.resize((VIDEO_WIDTH, VIDEO_HEIGHT))
                    processed.append(clip)
            
            if processed:
                bg_clip = concatenate_videoclips(processed, method="compose")
                if bg_clip.duration < total_duration:
                    bg_clip = bg_clip.loop(n=int(total_duration / bg_clip.duration) + 1)
                bg_clip = bg_clip.subclip(0, total_duration)
                bg_clip = bg_clip.fx(vfx.colorx, 0.5)  # Darken for text
            else:
                bg_clip = None
        else:
            bg_clip = None
        
        if bg_clip is None:
            # Fallback gradient
            gradient_img = create_gradient_background(VIDEO_WIDTH, VIDEO_HEIGHT, theme.background_gradient)
            bg_clip = pil_to_moviepy_clip(gradient_img, total_duration)
        
        # Create text overlays
        hook_img = create_fact_overlay(content.hook, VIDEO_WIDTH, 200, theme, "hook")
        fact_img = create_fact_overlay(content.main_text, VIDEO_WIDTH, 600, theme, "fact")
        source_img = create_fact_overlay(content.secondary_text or "", VIDEO_WIDTH, 100, theme, "source")
        
        hook_clip = pil_to_moviepy_clip(hook_img, 3).set_position(('center', 100)).set_start(0)
        fact_clip = pil_to_moviepy_clip(fact_img, total_duration - 3).set_position(('center', 'center')).set_start(3)
        source_clip = pil_to_moviepy_clip(source_img, 3).set_position(('center', VIDEO_HEIGHT - 200)).set_start(total_duration - 3)
        
        # Add voiceover
        vo_clip = AudioFileClip(str(voiceover_path))
        
        # Compose
        video = CompositeVideoClip([
            bg_clip,
            hook_clip,
            fact_clip,
            source_clip,
        ], size=(VIDEO_WIDTH, VIDEO_HEIGHT))
        
        # Set video duration to match voiceover + buffer
        actual_duration = min(total_duration, vo_clip.duration + 3)
        video = video.set_duration(actual_duration)
        video = video.set_audio(vo_clip.set_duration(min(vo_clip.duration, actual_duration)))
        
        # Render
        video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            preset='ultrafast',
            threads=4
        )
        
        print(f"   ✅ Generated: {output_path}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def generate_quote_video(content: VideoContent, output_path: str) -> bool:
    """Generate a quote/motivational video."""
    print(f"\n🎬 Generating quote video...")
    print(f"   Quote: {content.main_text[:50]}...")
    
    try:
        themes_list = list(THEMES.values())
        theme = random.choice(themes_list)
        
        # Generate voiceover
        voiceover_path = OUTPUT_DIR / "temp_vo.mp3"
        duration = await generate_voiceover_v2(content.voiceover_script, str(voiceover_path))
        
        total_duration = max(duration + 3, 12)
        
        # Get calming B-roll
        broll_clips = get_multiple_broll_clips(
            {"option_a": " ".join(content.broll_keywords or ["nature", "calm"]), "option_b": ""},
            count=2
        )
        
        # Create background
        if broll_clips and os.path.exists(broll_clips[0]):
            bg_clip = VideoFileClip(broll_clips[0])
            bg_clip = bg_clip.resize((VIDEO_WIDTH, VIDEO_HEIGHT))
            if bg_clip.duration < total_duration:
                bg_clip = bg_clip.loop(n=int(total_duration / bg_clip.duration) + 1)
            bg_clip = bg_clip.subclip(0, total_duration)
            bg_clip = bg_clip.fx(vfx.colorx, 0.6)
        else:
            gradient_img = create_gradient_background(VIDEO_WIDTH, VIDEO_HEIGHT, theme.background_gradient)
            bg_clip = pil_to_moviepy_clip(gradient_img, total_duration)
        
        # Create quote text
        quote_img = create_quote_overlay(content.main_text, content.secondary_text or "", VIDEO_WIDTH, VIDEO_HEIGHT)
        quote_clip = pil_to_moviepy_clip(quote_img, total_duration).set_position('center')
        
        # Hook
        hook_img = create_fact_overlay(content.hook, VIDEO_WIDTH, 150, theme, "hook")
        hook_clip = pil_to_moviepy_clip(hook_img, 2).set_position(('center', 50)).set_start(0)
        
        # Compose
        vo_clip = AudioFileClip(str(voiceover_path))
        
        video = CompositeVideoClip([
            bg_clip,
            quote_clip,
            hook_clip,
        ], size=(VIDEO_WIDTH, VIDEO_HEIGHT))
        
        # Set duration to match voiceover
        actual_duration = min(total_duration, vo_clip.duration + 3)
        video = video.set_duration(actual_duration)
        video = video.set_audio(vo_clip.set_duration(min(vo_clip.duration, actual_duration)))
        
        video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            preset='ultrafast',
            threads=4
        )
        
        print(f"   ✅ Generated: {output_path}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


# =============================================================================
# Helper Functions
# =============================================================================

def create_fact_overlay(text: str, width: int, height: int, 
                        theme: VideoTheme, style: str = "fact") -> Image.Image:
    """Create text overlay for facts."""
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Load font
    try:
        font_candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/System/Library/Fonts/Helvetica.ttc"
        ]
        font_path = next((f for f in font_candidates if os.path.exists(f)), None)
        
        if style == "hook":
            font_size = 48
        elif style == "source":
            font_size = 32
        else:
            font_size = 42
            
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # Word wrap
    words = text.split()
    lines = []
    current_line = []
    max_width = width - 80
    
    for word in words:
        current_line.append(word)
        test_line = " ".join(current_line)
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] > max_width:
            current_line.pop()
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    
    # Draw text with shadow
    y = 20
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (width - (bbox[2] - bbox[0])) // 2
        
        # Shadow
        draw.text((x + 3, y + 3), line, fill=(0, 0, 0, 180), font=font)
        # Main text
        color = theme.option_a_gradient[0] if style == "hook" else (255, 255, 255)
        draw.text((x, y), line, fill=(*color, 255), font=font)
        
        y += bbox[3] - bbox[1] + 10
    
    return img


def create_quote_overlay(quote: str, author: str, width: int, height: int) -> Image.Image:
    """Create a beautiful quote overlay."""
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font_candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "C:/Windows/Fonts/georgia.ttf",
        ]
        font_path = next((f for f in font_candidates if os.path.exists(f)), None)
        font_quote = ImageFont.truetype(font_path, 46) if font_path else ImageFont.load_default()
        font_author = ImageFont.truetype(font_path, 32) if font_path else ImageFont.load_default()
    except:
        font_quote = ImageFont.load_default()
        font_author = ImageFont.load_default()
    
    # Word wrap quote
    words = quote.split()
    lines = []
    current_line = []
    max_width = width - 100
    
    for word in words:
        current_line.append(word)
        test_line = " ".join(current_line)
        bbox = draw.textbbox((0, 0), test_line, font=font_quote)
        if bbox[2] - bbox[0] > max_width:
            current_line.pop()
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    
    # Calculate total height
    line_height = 60
    total_text_height = len(lines) * line_height + 50
    start_y = (height - total_text_height) // 2
    
    # Draw quote marks
    draw.text((50, start_y - 80), '"', fill=(255, 255, 255, 100), font=font_quote)
    
    # Draw lines
    y = start_y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_quote)
        x = (width - (bbox[2] - bbox[0])) // 2
        
        # Shadow
        draw.text((x + 2, y + 2), line, fill=(0, 0, 0, 150), font=font_quote)
        draw.text((x, y), line, fill=(255, 255, 255, 255), font=font_quote)
        
        y += line_height
    
    # Draw author
    if author:
        bbox = draw.textbbox((0, 0), author, font=font_author)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x + 2, y + 22), author, fill=(0, 0, 0, 150), font=font_author)
        draw.text((x, y + 20), author, fill=(200, 200, 200, 255), font=font_author)
    
    return img


# =============================================================================
# Main
# =============================================================================

async def main():
    parser = argparse.ArgumentParser(description="ViralShorts Factory - Multi-Type Generator")
    parser.add_argument("--type", choices=["wyr", "scary_facts", "money_facts", "ai_quotes", "kids", "random"],
                        default="random", help="Video type to generate")
    parser.add_argument("--count", type=int, default=1, help="Number of videos")
    parser.add_argument("--upload", action="store_true", help="Upload to YouTube")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎬 ViralShorts Factory - Multi-Type Generator")
    print("=" * 60)
    
    generator = MultiTypeContentGenerator()
    generated = 0
    
    for i in range(args.count):
        print(f"\n📹 Video {i+1}/{args.count}")
        
        # Get content based on type
        if args.type == "random":
            vtype = get_weighted_random_type()
        else:
            vtype = VideoType(args.type)
        
        if vtype == VideoType.SCARY_FACTS:
            content = generator.generate_scary_fact()
        elif vtype == VideoType.MONEY_FACTS:
            content = generator.generate_money_fact()
        elif vtype == VideoType.AI_QUOTES:
            content = generator.generate_quote()
        elif vtype == VideoType.KIDS:
            content = generator.generate_kids_content()
        else:
            content = generator.generate_wyr("Have unlimited money", "Have unlimited time")
        
        if not content:
            print("   ⚠️ Could not generate content")
            continue
        
        # Generate video
        output_path = str(OUTPUT_DIR / f"{vtype.value}_{random.randint(1000, 9999)}.mp4")
        
        if vtype in [VideoType.SCARY_FACTS, VideoType.MONEY_FACTS]:
            success = await generate_fact_video(content, output_path)
        elif vtype == VideoType.AI_QUOTES:
            success = await generate_quote_video(content, output_path)
        else:
            # Use WYR generator from script_v2
            from script_v2 import generate_professional_video_v2
            success = await generate_professional_video_v2(
                {"option_a": content.main_text, "option_b": content.secondary_text or "",
                 "percentage_a": content.percentage_a or 60},
                output_path
            )
        
        if success:
            generated += 1
    
    print(f"\n{'=' * 60}")
    print(f"✅ Generated {generated}/{args.count} videos")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())

