#!/usr/bin/env python3
"""
AI Video Quality Evaluator - Uses AI to assess generated video quality
For development only - evaluates and provides feedback on generated content
"""
import os
import json
from pathlib import Path
from typing import Dict, Optional

# Groq for fast evaluation
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

def evaluate_question_quality(question: Dict) -> Dict:
    """
    Evaluate a Would You Rather question for viral potential.
    Returns a score and suggestions.
    """
    if not GROQ_API_KEY:
        return {"score": 5, "feedback": "AI evaluation unavailable (no API key)"}
    
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        
        option_a = question.get("option_a", "")
        option_b = question.get("option_b", "")
        
        prompt = f"""Rate this "Would You Rather" question for viral YouTube Shorts potential.

Question: Would you rather...
A: {option_a}
B: {option_b}

Rate 1-10 on these criteria:
1. ENGAGEMENT: Will viewers debate in comments?
2. RELATABILITY: Can most people imagine both scenarios?
3. BALANCE: Are both options truly difficult to choose between?
4. HOOK: Does it grab attention immediately?
5. SHAREABILITY: Would viewers share this?

Return JSON only:
{{
  "overall_score": 1-10,
  "engagement": 1-10,
  "relatability": 1-10,
  "balance": 1-10,
  "hook": 1-10,
  "shareability": 1-10,
  "verdict": "VIRAL_WORTHY" or "NEEDS_WORK" or "SKIP",
  "suggestions": "1-2 sentence improvement suggestion"
}}"""
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a viral content expert. Rate questions honestly. Be harsh - only truly engaging content gets high scores."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        content = response.choices[0].message.content
        
        # Extract JSON
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group(0))
        
        return {"score": 5, "feedback": "Failed to parse AI response"}
        
    except Exception as e:
        return {"score": 5, "feedback": f"Evaluation error: {e}"}


def evaluate_video_concept(option_a: str, option_b: str, theme: str) -> Dict:
    """
    Evaluate the overall video concept before generation.
    Can save time by flagging low-quality content early.
    """
    if not GROQ_API_KEY:
        return {"should_generate": True, "score": 5}
    
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        
        prompt = f"""Quick assessment - should we generate a video for this content?

Question: Would you rather {option_a} OR {option_b}?
Visual Theme: {theme}

Criteria:
- Is this question interesting enough for YouTube Shorts?
- Will it generate comments and engagement?
- Is it appropriate and non-offensive?

Return JSON:
{{
  "should_generate": true/false,
  "score": 1-10,
  "reason": "1 sentence reason"
}}"""
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=150
        )
        
        content = response.choices[0].message.content
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            result = json.loads(json_match.group(0))
            return result
        
        return {"should_generate": True, "score": 5}
        
    except Exception as e:
        print(f"Evaluation error: {e}")
        return {"should_generate": True, "score": 5}


def batch_evaluate_questions(questions_file: str = "questions.json") -> None:
    """
    Evaluate all questions in the file and report quality stats.
    Useful for development to understand content quality.
    """
    if not os.path.exists(questions_file):
        print(f"Questions file not found: {questions_file}")
        return
    
    with open(questions_file, 'r') as f:
        questions = json.load(f)
    
    print(f"\n📊 Evaluating {len(questions)} questions...")
    
    scores = []
    viral_worthy = 0
    needs_work = 0
    skip = 0
    
    for i, q in enumerate(questions[:10]):  # Evaluate first 10 to save API calls
        result = evaluate_question_quality(q)
        score = result.get("overall_score", 5)
        verdict = result.get("verdict", "NEEDS_WORK")
        
        scores.append(score)
        
        if verdict == "VIRAL_WORTHY":
            viral_worthy += 1
            icon = "🔥"
        elif verdict == "SKIP":
            skip += 1
            icon = "⏭️"
        else:
            needs_work += 1
            icon = "📝"
        
        print(f"   {icon} Q{i+1}: Score {score}/10 - {verdict}")
        if result.get("suggestions"):
            print(f"      💡 {result['suggestions']}")
    
    if scores:
        avg_score = sum(scores) / len(scores)
        print(f"\n📈 Average Score: {avg_score:.1f}/10")
        print(f"   🔥 Viral Worthy: {viral_worthy}")
        print(f"   📝 Needs Work: {needs_work}")
        print(f"   ⏭️ Skip: {skip}")
        
        if avg_score < 5:
            print("\n⚠️ Content quality is LOW. Consider:")
            print("   - Using more engaging question templates")
            print("   - Adding trending topics")
            print("   - Making options more relatable")
        elif avg_score >= 7:
            print("\n✅ Content quality is GOOD!")


if __name__ == "__main__":
    # Run batch evaluation
    batch_evaluate_questions()

