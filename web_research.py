#!/usr/bin/env python3
"""
Web Research Automation
Uses built-in web_fetch to gather and summarize information
"""

import json
import re
from urllib.parse import urlparse

class WebResearcher:
    def __init__(self):
        self.session_history = []
    
    def validate_url(self, url):
        """Basic URL validation"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def extract_key_points(self, text, max_points=5):
        """Extract key points from text"""
        # Simple extraction based on sentence structure
        sentences = re.split(r'[.!?]+', text)
        
        # Filter for sentences that look like key points
        key_points = []
        for sent in sentences:
            sent = sent.strip()
            if len(sent) > 30 and len(sent) < 200:
                # Look for indicator words
                indicators = ['is', 'are', 'means', 'refers', 'used for', 'allows', 'enables', 'provides']
                if any(ind in sent.lower() for ind in indicators):
                    key_points.append(sent)
            if len(key_points) >= max_points:
                break
        
        return key_points
    
    def format_research_report(self, topic, sources, findings):
        """Format research into a readable report"""
        report = f"# Research Report: {topic}\n\n"
        report += f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        report += "## Sources\n\n"
        for i, source in enumerate(sources, 1):
            report += f"{i}. {source}\n"
        
        report += "\n## Key Findings\n\n"
        for finding in findings:
            report += f"- {finding}\n"
        
        report += "\n## Summary\n\n"
        report += f"Research on '{topic}' completed. Review findings above.\n"
        
        return report
    
    def save_research(self, topic, report):
        """Save research to memory folder"""
        from datetime import datetime
        from pathlib import Path
        
        safe_topic = re.sub(r'[^\w\s-]', '', topic).replace(' ', '_')[:30]
        filename = f"research_{safe_topic}_{datetime.now().strftime('%Y%m%d')}.md"
        filepath = Path("/root/.openclaw/workspace/memory") / filename
        
        with open(filepath, 'w') as f:
            f.write(report)
        
        return str(filepath)

# Helper function for external use
def quick_research_summary(text_content, max_points=5):
    """Extract summary from fetched content"""
    researcher = WebResearcher()
    return researcher.extract_key_points(text_content, max_points)

if __name__ == "__main__":
    print("Web Research utilities loaded.")
    print("Usage: Import and use WebResearcher class")
    print("Or call quick_research_summary(text) for simple extraction")
