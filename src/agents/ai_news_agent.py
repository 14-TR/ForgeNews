"""
AI News Agent for the ForgeNews platform.
Ingests and summarizes bleeding-edge AI headlines.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

# Add the parent directory to the Python path to make imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Mock data for AI news headlines (in production, this would be from a real source)
MOCK_AI_NEWS = [
    {
        "title": "OpenAI Unveils GPT-5 with Unprecedented Reasoning Capabilities",
        "date": "2025-04-15",
        "source": "TechCrunch",
        "summary": "OpenAI has released GPT-5, demonstrating significant improvements in reasoning, planning, and factual accuracy."
    },
    {
        "title": "Google Introduces Multisensory AI Model That Can See, Hear and Touch",
        "date": "2025-04-14",
        "source": "The Verge",
        "summary": "Google's DeepMind has created a unified model that integrates visual, auditory and tactile sensing capabilities."
    },
    {
        "title": "EU AI Act Enforcement Begins with Focus on High-Risk Applications",
        "date": "2025-04-12",
        "source": "Reuters",
        "summary": "The EU has begun enforcing its comprehensive AI legislation with particular attention to AI systems deemed high-risk."
    },
    {
        "title": "Anthropic Releases Breakthrough Paper on AI Alignment Techniques",
        "date": "2025-04-10",
        "source": "VentureBeat",
        "summary": "Anthropic has published research on new methods to align advanced AI systems with human values and intentions."
    },
    {
        "title": "Neural Interfaces Achieve New Milestone in Brain-Computer Integration",
        "date": "2025-04-08",
        "source": "Nature",
        "summary": "Researchers have demonstrated a neural interface that allows for precise two-way communication between the brain and computers."
    }
]

def fetch_ai_news() -> List[Dict[str, str]]:
    """
    Fetch the latest AI news headlines.
    In production, this would connect to real news APIs or web scraping.
    Currently returns mock data.
    """
    return MOCK_AI_NEWS

def analyze_trends(news_items: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Analyze trends in AI news headlines.
    """
    # Simple categorization of news
    categories = {
        "product_releases": 0,
        "research": 0,
        "policy": 0,
        "business": 0,
        "other": 0
    }
    
    for item in news_items:
        title = item["title"].lower()
        summary = item["summary"].lower()
        
        if any(word in title or word in summary for word in ["release", "unveil", "launch", "introduce"]):
            categories["product_releases"] += 1
        elif any(word in title or word in summary for word in ["research", "paper", "study", "discover"]):
            categories["research"] += 1
        elif any(word in title or word in summary for word in ["policy", "regulation", "law", "compliance", "act"]):
            categories["policy"] += 1
        elif any(word in title or word in summary for word in ["funding", "acquisition", "startup", "investment"]):
            categories["business"] += 1
        else:
            categories["other"] += 1
    
    # Determine the dominant trend
    dominant_category = max(categories, key=categories.get)
    
    return {
        "category_counts": categories,
        "dominant_trend": dominant_category,
        "total_news_items": len(news_items)
    }

def summarize_headlines(news_items: List[Dict[str, str]]) -> str:
    """
    Generate a summary of the key AI headlines.
    """
    if not news_items:
        return "No AI news headlines available."
    
    trend_analysis = analyze_trends(news_items)
    
    # Generate the summary
    summary = f"AI News Summary ({datetime.now().strftime('%Y-%m-%d')})\n\n"
    summary += f"Analyzed {trend_analysis['total_news_items']} recent AI news items.\n"
    summary += f"Dominant trend: {trend_analysis['dominant_trend'].replace('_', ' ').title()}\n\n"
    
    summary += "Key Headlines:\n"
    for i, item in enumerate(news_items[:3], 1):
        summary += f"{i}. {item['title']} ({item['source']}, {item['date']})\n"
        summary += f"   {item['summary']}\n\n"
    
    return summary

def save_news_summary(summary: str) -> None:
    """
    Save the news summary to a file.
    """
    output_dir = os.path.join("data", "processed", "ai_news")
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"ai_news_summary_{datetime.now().strftime('%Y%m%d')}.txt"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, "w") as f:
        f.write(summary)
    
    print(f"[ai_news_agent] Saved news summary to {filepath}")

def run() -> Dict[str, Any]:
    """
    Main entry point for the AI news agent.
    """
    try:
        print("[ai_news_agent] Fetching AI news headlines...")
        news_items = fetch_ai_news()
        
        print(f"[ai_news_agent] Retrieved {len(news_items)} news items")
        news_summary = summarize_headlines(news_items)
        
        save_news_summary(news_summary)
        
        return {
            "status": "success",
            "news_count": len(news_items),
            "output": "AI news summary generated successfully"
        }
    except Exception as e:
        print(f"[ai_news_agent] Error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        } 