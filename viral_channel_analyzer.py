#!/usr/bin/env python3
"""
ViralShorts Factory - Viral Channel Analyzer v1.0
===================================================

Learns from "graduated" channels (1000+ subs, monetized):
1. Finds successful AI-generated Shorts channels
2. Analyzes their most viral content
3. Extracts patterns (titles, hooks, lengths, categories)
4. Feeds patterns back into our generation system

This is the "learn from the pros" system!
"""

import os
import json
import re
import random
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Try to import persistent state
try:
    from persistent_state import get_viral_manager, safe_print
except ImportError:
    def safe_print(msg): 
        try: print(msg)
        except: print(re.sub(r'[^\x00-\x7F]+', '', msg))
    get_viral_manager = None


@dataclass
class ChannelInsight:
    """Insights extracted from a successful channel."""
    channel_name: str
    subscriber_count: int
    avg_views_per_short: int
    top_performing_titles: List[str]
    common_title_patterns: List[str]
    hook_techniques: List[str]
    avg_video_length: int  # seconds
    posting_frequency: str
    niche: str


class ViralChannelAnalyzer:
    """
    Analyzes successful Shorts channels to learn winning patterns.
    
    Uses:
    - YouTube Data API for channel/video data
    - AI to extract patterns and insights
    """
    
    # Known successful AI-generated Shorts channels to study
    # These are "graduated" channels that hit monetization
    REFERENCE_CHANNELS = [
        # Facts/Trivia channels
        "UCQb8fMCz9sOMcR9GfqLJ3kQ",  # Example: facts channel
        "UC2JhO3f8dJ3xSY1dGqr0AZw",  # Example: psychology facts
        # Add more known successful channels here
    ]
    
    # Patterns we've learned from manual research
    PROVEN_PATTERNS = {
        "title_formulas": [
            "{Number}% of people can't do this",
            "This {thing} will blow your mind",
            "Watch till the end for the reveal",
            "Only {type} people understand this",
            "What happens if you {action}?",
            "The truth about {topic} no one tells you",
            "I tested {claim} and here's what happened",
            "You've been doing {action} wrong",
            "Why {thing} is {adjective}er than you think",
            "This {number} second trick changes everything"
        ],
        "hook_techniques": [
            "Pattern interrupt (STOP, WAIT, HOLD UP)",
            "Question opener (Did you know...?)",
            "Controversy hook (Everyone thinks X but actually Y)",
            "Curiosity gap (What I'm about to show you...)",
            "Challenge hook (Try this and see if you can...)",
            "Urgency hook (Before this gets taken down...)",
            "Social proof (Millions of people don't know this)",
            "Personal story (I just discovered something...)"
        ],
        "engagement_tactics": [
            "End with question forcing comment",
            "Ask for prediction before reveal",
            "Create poll-like choices (A or B?)",
            "Promise part 2 for followers",
            "Time-limited exclusive content",
            "Save for later CTA",
            "Share with someone who needs this"
        ],
        "optimal_metrics": {
            "video_length_seconds": (15, 25),  # Sweet spot
            "hook_length_seconds": (1, 3),      # First 1-3 seconds critical
            "phrases_count": (3, 5),            # Not too many
            "words_per_phrase": (8, 15)         # Short, punchy
        }
    }
    
    def __init__(self):
        self.youtube_api_key = os.environ.get("YOUTUBE_API_KEY")
        self.groq_key = os.environ.get("GROQ_API_KEY")
        
        # Load any previously learned patterns
        if get_viral_manager:
            self.viral_manager = get_viral_manager()
        else:
            self.viral_manager = None
    
    def analyze_channel(self, channel_id: str) -> Optional[ChannelInsight]:
        """
        Analyze a YouTube channel to extract viral patterns.
        
        Requires YouTube Data API key.
        """
        if not self.youtube_api_key:
            safe_print("[!] No YouTube API key for channel analysis")
            return None
        
        try:
            # Get channel info
            channel_url = f"https://www.googleapis.com/youtube/v3/channels"
            params = {
                "key": self.youtube_api_key,
                "id": channel_id,
                "part": "statistics,snippet,contentDetails"
            }
            
            response = requests.get(channel_url, params=params, timeout=15)
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not data.get("items"):
                return None
            
            channel = data["items"][0]
            stats = channel.get("statistics", {})
            snippet = channel.get("snippet", {})
            
            subscriber_count = int(stats.get("subscriberCount", 0))
            
            # Only analyze "graduated" channels (1000+ subs)
            if subscriber_count < 1000:
                safe_print(f"[SKIP] Channel {channel_id} has {subscriber_count} subs (need 1000+)")
                return None
            
            # Get recent Shorts videos
            uploads_playlist = channel["contentDetails"]["relatedPlaylists"]["uploads"]
            videos = self._get_channel_shorts(uploads_playlist)
            
            if not videos:
                return None
            
            # Analyze video patterns
            avg_views = sum(v["views"] for v in videos) / len(videos) if videos else 0
            top_titles = [v["title"] for v in sorted(videos, key=lambda x: x["views"], reverse=True)[:10]]
            
            # Extract patterns using AI
            patterns = self._extract_patterns_with_ai(top_titles)
            
            return ChannelInsight(
                channel_name=snippet.get("title", "Unknown"),
                subscriber_count=subscriber_count,
                avg_views_per_short=int(avg_views),
                top_performing_titles=top_titles,
                common_title_patterns=patterns.get("title_patterns", []),
                hook_techniques=patterns.get("hook_techniques", []),
                avg_video_length=patterns.get("avg_length", 20),
                posting_frequency=patterns.get("posting_frequency", "daily"),
                niche=patterns.get("niche", "general")
            )
            
        except Exception as e:
            safe_print(f"[!] Channel analysis error: {e}")
            return None
    
    def _get_channel_shorts(self, playlist_id: str, max_results: int = 20) -> List[Dict]:
        """Get Shorts from channel's uploads playlist."""
        if not self.youtube_api_key:
            return []
        
        try:
            url = "https://www.googleapis.com/youtube/v3/playlistItems"
            params = {
                "key": self.youtube_api_key,
                "playlistId": playlist_id,
                "part": "snippet",
                "maxResults": max_results
            }
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code != 200:
                return []
            
            items = response.json().get("items", [])
            video_ids = [item["snippet"]["resourceId"]["videoId"] for item in items]
            
            # Get video statistics
            videos_url = "https://www.googleapis.com/youtube/v3/videos"
            videos_params = {
                "key": self.youtube_api_key,
                "id": ",".join(video_ids),
                "part": "statistics,contentDetails,snippet"
            }
            
            videos_response = requests.get(videos_url, params=videos_params, timeout=15)
            if videos_response.status_code != 200:
                return []
            
            videos = []
            for item in videos_response.json().get("items", []):
                duration = item["contentDetails"].get("duration", "PT0S")
                # Only include Shorts (< 60 seconds)
                if self._duration_to_seconds(duration) <= 60:
                    videos.append({
                        "id": item["id"],
                        "title": item["snippet"]["title"],
                        "views": int(item["statistics"].get("viewCount", 0)),
                        "likes": int(item["statistics"].get("likeCount", 0)),
                        "comments": int(item["statistics"].get("commentCount", 0)),
                        "duration": self._duration_to_seconds(duration)
                    })
            
            return videos
            
        except Exception as e:
            safe_print(f"[!] Error getting Shorts: {e}")
            return []
    
    def _duration_to_seconds(self, duration: str) -> int:
        """Convert ISO 8601 duration to seconds."""
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if not match:
            return 0
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds
    
    def _extract_patterns_with_ai(self, titles: List[str]) -> Dict:
        """Use AI to extract patterns from successful titles."""
        if not self.groq_key or not titles:
            return {}
        
        prompt = f"""Analyze these viral YouTube Shorts titles and extract reusable patterns:

TITLES:
{json.dumps(titles, indent=2)}

Extract:
1. Title patterns/formulas that could be reused
2. Hook techniques used
3. Common themes/niches
4. Word count patterns

Return JSON:
{{
    "title_patterns": ["pattern with {{placeholders}}", ...],
    "hook_techniques": ["technique 1", ...],
    "niche": "main category",
    "avg_word_count": number
}}

JSON ONLY."""

        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                timeout=15
            )
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                match = re.search(r'\{[\s\S]*\}', content)
                if match:
                    return json.loads(match.group())
        except Exception as e:
            safe_print(f"[!] AI pattern extraction error: {e}")
        
        return {}
    
    def get_viral_patterns(self) -> Dict:
        """
        Get all learned viral patterns (from file + hardcoded research).
        
        Returns comprehensive patterns for video generation.
        """
        patterns = self.PROVEN_PATTERNS.copy()
        
        # Merge with saved patterns from viral manager
        if self.viral_manager:
            saved = self.viral_manager.patterns
            for key in ["title_patterns", "hook_patterns", "engagement_baits"]:
                if key in saved:
                    patterns_key = key.replace("_patterns", "_formulas") if "title" in key else key
                    if patterns_key not in patterns:
                        patterns_key = key
                    existing = patterns.get(patterns_key, [])
                    for item in saved[key]:
                        if item not in existing:
                            existing.append(item)
                    patterns[patterns_key] = existing
        
        return patterns
    
    def get_optimized_prompt_additions(self) -> str:
        """
        Get prompt additions based on viral patterns.
        
        Add this to video generation prompts for better virality.
        """
        patterns = self.get_viral_patterns()
        
        sample_titles = random.sample(patterns.get("title_formulas", []), min(3, len(patterns.get("title_formulas", []))))
        sample_hooks = random.sample(patterns.get("hook_techniques", []), min(2, len(patterns.get("hook_techniques", []))))
        
        return f"""
=== VIRAL PATTERNS (Learned from successful channels) ===

TITLE FORMULAS that get views:
{chr(10).join(f'- {t}' for t in sample_titles)}

HOOK TECHNIQUES that stop the scroll:
{chr(10).join(f'- {h}' for h in sample_hooks)}

OPTIMAL METRICS:
- Video length: 15-25 seconds (CRITICAL!)
- Hook: First 1-3 seconds must grab attention
- Phrases: 3-5 short phrases (8-15 words each)
- End with engagement question

ENGAGEMENT BAITS (use one at the end):
{chr(10).join(f'- {e}' for e in random.sample(patterns.get("engagement_tactics", ["Comment below!"]), 2))}
"""
    
    def learn_from_our_best(self, our_videos: List[Dict]) -> Dict:
        """
        Analyze our own best-performing videos to learn what works for us.
        
        This is the self-improvement loop!
        """
        if not our_videos:
            return {}
        
        # Sort by views/engagement
        sorted_videos = sorted(our_videos, 
                               key=lambda x: x.get("views", 0) + x.get("likes", 0) * 10, 
                               reverse=True)
        
        top_videos = sorted_videos[:5]
        
        # Extract our best patterns
        best_categories = [v.get("category") for v in top_videos if v.get("category")]
        best_hooks = [v.get("hook") for v in top_videos if v.get("hook")]
        
        patterns = {
            "our_best_categories": list(set(best_categories)),
            "our_best_hooks": best_hooks[:3],
            "avg_best_length": sum(v.get("duration", 20) for v in top_videos) / len(top_videos) if top_videos else 20
        }
        
        safe_print(f"[LEARN] Our best categories: {patterns['our_best_categories']}")
        
        return patterns


def get_viral_prompt_boost() -> str:
    """
    Quick function to get viral pattern additions for prompts.
    
    Use this in video generation prompts!
    """
    analyzer = ViralChannelAnalyzer()
    return analyzer.get_optimized_prompt_additions()


def analyze_and_update_patterns():
    """
    Main function to analyze channels and update our patterns.
    
    Run this periodically to keep patterns fresh.
    """
    analyzer = ViralChannelAnalyzer()
    
    safe_print("\n" + "=" * 60)
    safe_print("   VIRAL CHANNEL ANALYZER")
    safe_print("=" * 60)
    
    # Get current patterns
    patterns = analyzer.get_viral_patterns()
    safe_print(f"\n   Title formulas: {len(patterns.get('title_formulas', []))}")
    safe_print(f"   Hook techniques: {len(patterns.get('hook_techniques', []))}")
    safe_print(f"   Engagement tactics: {len(patterns.get('engagement_tactics', []))}")
    
    # Sample output
    safe_print("\n   Sample viral additions for prompts:")
    safe_print("-" * 50)
    print(analyzer.get_optimized_prompt_additions())
    
    return patterns


if __name__ == "__main__":
    analyze_and_update_patterns()

