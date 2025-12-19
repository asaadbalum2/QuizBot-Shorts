#!/usr/bin/env python3
"""
Background Music Fetcher - Gets free, copyright-safe music
Uses Jamendo API (free, no credit card required)
"""
import os
import random
import requests
from pathlib import Path
from typing import Optional, List

MUSIC_DIR = Path("./assets/music")
MUSIC_DIR.mkdir(parents=True, exist_ok=True)

# Jamendo API - FREE, no credit card, copyright-safe for YouTube
JAMENDO_BASE_URL = "https://api.jamendo.com/v3.0"
JAMENDO_CLIENT_ID = "58c7c0f1"  # Public client ID (free tier)

# Mood to music tag mapping
MOOD_TAGS = {
    "fun": ["happy", "upbeat", "playful"],
    "dramatic": ["epic", "cinematic", "dramatic"],
    "mysterious": ["ambient", "dark", "atmospheric"],
    "energetic": ["energetic", "electronic", "dance"],
    "chill": ["chill", "ambient", "calm"],
    "default": ["pop", "electronic", "ambient"]
}


def get_background_music(mood: str = "fun", duration: float = 45) -> Optional[str]:
    """
    Fetch background music matching the mood.
    Returns path to downloaded MP3 or None.
    Tries multiple free sources with fallbacks.
    """
    print(f"   🎵 Searching for {mood} music...")
    
    # Check for cached music first
    cached = _get_cached_music(mood)
    if cached:
        print(f"   ✅ Using cached music")
        return cached
    
    # Try Jamendo API (large library, free)
    music_path = _fetch_jamendo_music(mood)
    if music_path:
        return music_path
    
    # Try FreePD (public domain, always works)
    music_path = _fetch_freepd_music(mood)
    if music_path:
        return music_path
    
    # Try Pixabay Music (if API key available)
    music_path = _fetch_pixabay_music(mood)
    if music_path:
        return music_path
    
    # Last resort: Use any cached music
    all_cached = list(MUSIC_DIR.glob("**/*.mp3"))
    if all_cached:
        chosen = random.choice(all_cached)
        print(f"   ⚠️ Using fallback music: {chosen.name}")
        return str(chosen)
    
    print("   ⚠️ No background music available")
    return None


def _get_cached_music(mood: str) -> Optional[str]:
    """Check for cached music files."""
    mood_dir = MUSIC_DIR / mood
    if mood_dir.exists():
        mp3_files = list(mood_dir.glob("*.mp3"))
        if mp3_files:
            return str(random.choice(mp3_files))
    
    # Check general music folder
    mp3_files = list(MUSIC_DIR.glob("*.mp3"))
    if mp3_files:
        return str(random.choice(mp3_files))
    
    return None


def _fetch_jamendo_music(mood: str) -> Optional[str]:
    """Fetch music from Jamendo API with multiple fallback strategies."""
    tags_to_try = [
        MOOD_TAGS.get(mood, MOOD_TAGS["default"]),
        ["instrumental", "background"],
        ["electronic", "ambient"],
        ["pop", "happy"]
    ]
    
    for tags in tags_to_try:
        try:
            params = {
                "client_id": JAMENDO_CLIENT_ID,
                "format": "json",
                "limit": 30,
                "tags": "+".join(tags[:2]),
                "order": "popularity_total",  # Most popular overall
                "audioformat": "mp32",
            }
            
            response = requests.get(
                f"{JAMENDO_BASE_URL}/tracks",
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                tracks = data.get("results", [])
                
                if tracks:
                    track = random.choice(tracks[:min(10, len(tracks))])
                    audio_url = track.get("audio", "")
                    
                    if audio_url:
                        result = _download_music(
                            audio_url,
                            f"jamendo_{track.get('id', 'unknown')}",
                            mood
                        )
                        if result:
                            print(f"   🎵 Got music: {track.get('name', 'Unknown')}")
                            return result
        except Exception as e:
            continue
    
    print(f"⚠️ Jamendo API failed for all tag combinations")
    return None


def _fetch_freepd_music(mood: str) -> Optional[str]:
    """Fetch music from FreePD (truly free public domain music)."""
    # FreePD categories - all public domain, no attribution needed
    mood_to_genre = {
        "fun": "upbeat",
        "dramatic": "epic",
        "energetic": "electronic",
        "chill": "ambient",
        "default": "misc"
    }
    
    genre = mood_to_genre.get(mood, "misc")
    
    # Known working FreePD tracks (public domain)
    freepd_tracks = {
        "upbeat": "https://freepd.com/music/Happy%20Fun%20Times.mp3",
        "epic": "https://freepd.com/music/Epic%20Cinematic.mp3",
        "electronic": "https://freepd.com/music/Synthwave%20Beat.mp3",
        "ambient": "https://freepd.com/music/Ambient%20Background.mp3",
        "misc": "https://freepd.com/music/Background%20Music.mp3"
    }
    
    url = freepd_tracks.get(genre, freepd_tracks["misc"])
    
    try:
        return _download_music(url, f"freepd_{genre}", mood)
    except:
        return None


def _fetch_pixabay_music(mood: str) -> Optional[str]:
    """Fetch music from Pixabay (requires API key)."""
    api_key = os.environ.get("PIXABAY_API_KEY", "")
    if not api_key:
        return None
    
    try:
        tags = MOOD_TAGS.get(mood, MOOD_TAGS["default"])
        
        params = {
            "key": api_key,
            "q": tags[0],
            "category": "music",
            "per_page": 10,
            "order": "popular"
        }
        
        response = requests.get(
            "https://pixabay.com/api/",
            params=params,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            hits = data.get("hits", [])
            if hits:
                track = random.choice(hits)
                audio_url = track.get("videos", {}).get("medium", {}).get("url", "")
                if audio_url:
                    return _download_music(audio_url, f"pixabay_{track.get('id')}", mood)
        
        return None
        
    except Exception as e:
        print(f"⚠️ Pixabay API error: {e}")
        return None


def _download_music(url: str, track_id: str, mood: str) -> Optional[str]:
    """Download and cache music file."""
    try:
        mood_dir = MUSIC_DIR / mood
        mood_dir.mkdir(parents=True, exist_ok=True)
        
        music_path = mood_dir / f"{track_id}.mp3"
        
        # Check cache
        if music_path.exists() and music_path.stat().st_size > 10000:
            print(f"🎵 Using cached: {music_path.name}")
            return str(music_path)
        
        # Download
        print(f"🎵 Downloading music: {track_id}...")
        response = requests.get(url, timeout=60, stream=True)
        response.raise_for_status()
        
        with open(music_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        if music_path.exists() and music_path.stat().st_size > 10000:
            print(f"✅ Music downloaded: {music_path.name}")
            return str(music_path)
        
        return None
        
    except Exception as e:
        print(f"⚠️ Music download error: {e}")
        return None


def get_mood_for_question(option_a: str, option_b: str) -> str:
    """Determine the mood based on question content."""
    text = f"{option_a} {option_b}".lower()
    
    if any(word in text for word in ["money", "rich", "million", "billion", "wealthy"]):
        return "energetic"
    elif any(word in text for word in ["die", "death", "never", "forever", "scary"]):
        return "dramatic"
    elif any(word in text for word in ["super", "power", "fly", "invisible", "magic"]):
        return "fun"
    elif any(word in text for word in ["love", "relationship", "friend", "family"]):
        return "chill"
    else:
        return "fun"


if __name__ == "__main__":
    # Test
    music = get_background_music("fun")
    print(f"Result: {music}")

