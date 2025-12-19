#!/usr/bin/env python3
"""
Background Music Fetcher - Gets free, copyright-safe music
Uses REAL working sources with verified URLs
"""
import os
import random
import requests
from pathlib import Path
from typing import Optional, List

MUSIC_DIR = Path("./assets/music")
MUSIC_DIR.mkdir(parents=True, exist_ok=True)

# Using Pixabay's free music API (no API key needed for some endpoints)
# These are ACTUAL working URLs from Pixabay's CDN
PIXABAY_MUSIC_URLS = {
    "fun": [
        # Fun, upbeat (Pixabay free music - CC0)
        "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8cb749d484.mp3",  # Happy Day
        "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0c6ff1c94.mp3",  # Upbeat Fun
        "https://cdn.pixabay.com/download/audio/2021/11/25/audio_91b32e02f9.mp3",  # Cheerful
    ],
    "dramatic": [
        # Epic, cinematic
        "https://cdn.pixabay.com/download/audio/2022/02/22/audio_d1718ab41b.mp3",  # Epic Cinematic
        "https://cdn.pixabay.com/download/audio/2022/05/16/audio_d44b2d1089.mp3",  # Dramatic
    ],
    "energetic": [
        # Electronic, upbeat
        "https://cdn.pixabay.com/download/audio/2022/03/10/audio_70bdd56cf6.mp3",  # Electronic
        "https://cdn.pixabay.com/download/audio/2022/10/25/audio_398e13b76e.mp3",  # Energy
    ],
    "chill": [
        # Calm, ambient
        "https://cdn.pixabay.com/download/audio/2022/05/27/audio_a15cea5c15.mp3",  # Lofi Chill
        "https://cdn.pixabay.com/download/audio/2022/01/20/audio_0a8e1e4c15.mp3",  # Ambient
    ],
    "mystery": [
        # Mysterious, tense
        "https://cdn.pixabay.com/download/audio/2022/03/15/audio_942694cbd3.mp3",  # Suspense
    ],
}

# Backup: Chosic free music (reliable CDN)
CHOSIC_MUSIC_URLS = {
    "fun": "https://www.chosic.com/wp-content/uploads/2021/07/Happy-Summer-Show-chosic.com_.mp3",
    "dramatic": "https://www.chosic.com/wp-content/uploads/2021/05/Epic-Cinematic-Action-chosic.com_.mp3",
    "energetic": "https://www.chosic.com/wp-content/uploads/2021/06/Electronic-Rock-chosic.com_.mp3",
    "chill": "https://www.chosic.com/wp-content/uploads/2021/04/Lofi-Study-chosic.com_.mp3",
}

# NOTE: Removed pydub tone generation - it sounded like broken radio!
# Better to have NO music than bad generated tones.


def get_background_music(mood: str = "fun", duration: float = 45) -> Optional[str]:
    """
    Fetch REAL background music matching the mood.
    Returns path to downloaded MP3 or None.
    NO GENERATED TONES - only real music or nothing.
    """
    print(f"   🎵 Getting {mood} background music...")
    
    # Check for cached music first
    cached = _get_cached_music(mood)
    if cached:
        print(f"   ✅ Using cached music: {Path(cached).name}")
        return cached
    
    # Try Pixabay music (most reliable)
    pixabay_urls = PIXABAY_MUSIC_URLS.get(mood, PIXABAY_MUSIC_URLS.get("fun", []))
    random.shuffle(pixabay_urls)  # Randomize
    
    for url in pixabay_urls:
        try:
            music_path = _download_music(url, mood)
            if music_path:
                print(f"   ✅ Got Pixabay music")
                return music_path
        except Exception as e:
            print(f"   ⚠️ Pixabay download failed: {e}")
            continue
    
    # Try Chosic backup
    chosic_url = CHOSIC_MUSIC_URLS.get(mood, CHOSIC_MUSIC_URLS.get("fun"))
    if chosic_url:
        try:
            music_path = _download_music(chosic_url, mood)
            if music_path:
                print(f"   ✅ Got Chosic music")
                return music_path
        except Exception as e:
            print(f"   ⚠️ Chosic download failed: {e}")
    
    # Last resort: Use any cached music
    all_cached = list(MUSIC_DIR.glob("**/*.mp3"))
    valid_cached = [f for f in all_cached if f.stat().st_size > 50000]  # At least 50KB
    if valid_cached:
        chosen = random.choice(valid_cached)
        print(f"   ⚠️ Using fallback cached: {chosen.name}")
        return str(chosen)
    
    # NO GENERATED TONES - better to have no music than broken radio sound
    print("   ⚠️ No background music available (skipping - better than bad audio)")
    return None


def _get_cached_music(mood: str) -> Optional[str]:
    """Check for cached music files."""
    mood_dir = MUSIC_DIR / mood
    if mood_dir.exists():
        mp3_files = list(mood_dir.glob("*.mp3"))
        if mp3_files:
            # Only use files > 10KB (valid mp3)
            valid = [f for f in mp3_files if f.stat().st_size > 10000]
            if valid:
                return str(random.choice(valid))
    
    # Check general music folder
    mp3_files = list(MUSIC_DIR.glob("*.mp3"))
    valid = [f for f in mp3_files if f.stat().st_size > 10000]
    if valid:
        return str(random.choice(valid))
    
    return None


def _download_music(url: str, mood: str) -> Optional[str]:
    """Download and cache music file."""
    try:
        mood_dir = MUSIC_DIR / mood
        mood_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename from URL
        filename = url.split("/")[-1].replace("%20", "_")
        if not filename.endswith(".mp3"):
            filename += ".mp3"
        
        music_path = mood_dir / filename
        
        # Check cache
        if music_path.exists() and music_path.stat().st_size > 10000:
            return str(music_path)
        
        # Download with timeout
        print(f"   🎵 Downloading: {filename}...")
        response = requests.get(url, timeout=30, stream=True, 
                               headers={'User-Agent': 'Mozilla/5.0'})
        
        if response.status_code != 200:
            print(f"   ⚠️ HTTP {response.status_code} for {url}")
            return None
        
        with open(music_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        if music_path.exists() and music_path.stat().st_size > 10000:
            print(f"   ✅ Downloaded: {filename}")
            return str(music_path)
        else:
            # Delete invalid file
            if music_path.exists():
                music_path.unlink()
            return None
        
    except Exception as e:
        print(f"   ⚠️ Music download error: {e}")
        return None


def get_mood_for_question(option_a: str, option_b: str) -> str:
    """Determine the mood based on question content."""
    text = f"{option_a} {option_b}".lower()
    
    if any(word in text for word in ["money", "rich", "million", "billion", "wealthy", "salary"]):
        return "energetic"
    elif any(word in text for word in ["die", "death", "never", "forever", "scary", "horror", "ghost"]):
        return "dramatic"
    elif any(word in text for word in ["super", "power", "fly", "invisible", "magic", "teleport"]):
        return "fun"
    elif any(word in text for word in ["love", "relationship", "friend", "family", "date"]):
        return "chill"
    elif any(word in text for word in ["secret", "mystery", "hidden", "unknown"]):
        return "mystery"
    else:
        return "fun"


if __name__ == "__main__":
    # Test
    print("Testing background music fetcher...")
    for mood in ["fun", "dramatic", "energetic"]:
        print(f"\n--- Testing mood: {mood} ---")
        music = get_background_music(mood)
        print(f"Result: {music}")
