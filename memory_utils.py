#!/usr/bin/env python3
"""
Enhanced Memory Utilities
File-based memory system with improved search and organization
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path("/root/.openclaw/workspace/memory")
MEMORY_FILE = Path("/root/.openclaw/workspace/MEMORY.md")

class MemoryManager:
    def __init__(self):
        self.memory_dir = MEMORY_DIR
        self.memory_file = MEMORY_FILE
        self.memory_dir.mkdir(exist_ok=True)
        
    def search_memory(self, query, max_results=5):
        """Search all memory files for relevant content"""
        results = []
        query_lower = query.lower()
        
        # Search MEMORY.md
        if self.memory_file.exists():
            with open(self.memory_file, 'r') as f:
                content = f.read()
                if query_lower in content.lower():
                    # Find context around match
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if query_lower in line.lower():
                            start = max(0, i - 2)
                            end = min(len(lines), i + 3)
                            context = '\n'.join(lines[start:end])
                            results.append({
                                'source': 'MEMORY.md',
                                'line': i + 1,
                                'context': context
                            })
                            break
        
        # Search daily memory files
        for mem_file in sorted(self.memory_dir.glob("*.md")):
            if mem_file.name == "conversations":
                continue
            with open(mem_file, 'r') as f:
                content = f.read()
                if query_lower in content.lower():
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if query_lower in line.lower():
                            start = max(0, i - 2)
                            end = min(len(lines), i + 3)
                            context = '\n'.join(lines[start:end])
                            results.append({
                                'source': mem_file.name,
                                'line': i + 1,
                                'context': context
                            })
                            break
        
        return results[:max_results]
    
    def add_memory(self, category, content, importance="normal"):
        """Add a new memory entry to MEMORY.md"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        entry = f"\n## {category} - {timestamp}\n\n{content}\n\n---\n"
        
        with open(self.memory_file, 'a') as f:
            f.write(entry)
        
        return f"Added to MEMORY.md: {category}"
    
    def get_recent_context(self, days=7):
        """Get recent memory entries from last N days"""
        recent = []
        today = datetime.now()
        
        for mem_file in sorted(self.memory_dir.glob("*.md"), reverse=True)[:days]:
            if mem_file.exists():
                with open(mem_file, 'r') as f:
                    content = f.read()
                    recent.append({
                        'date': mem_file.stem,
                        'content': content[:2000]  # First 2000 chars
                    })
        
        return recent
    
    def summarize_conversations(self, date_str=None):
        """Summarize conversations from a specific date"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        conv_file = self.memory_dir / f"conversations/{date_str}_conversation.md"
        
        if not conv_file.exists():
            return f"No conversations found for {date_str}"
        
        with open(conv_file, 'r') as f:
            content = f.read()
        
        # Count messages
        scott_msgs = content.count('**Scott:**')
        aimee_msgs = content.count('**Aimee:**')
        
        return {
            'date': date_str,
            'scott_messages': scott_msgs,
            'aimee_messages': aimee_msgs,
            'preview': content[:500] + "..." if len(content) > 500 else content
        }

if __name__ == "__main__":
    mm = MemoryManager()
    
    # Test search
    print("Testing memory search...")
    results = mm.search_memory("trading", max_results=3)
    for r in results:
        print(f"\n{r['source']} (line {r['line']}):")
        print(r['context'][:200])
