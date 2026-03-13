#!/usr/bin/env python3
"""
log_chat.py - Append conversation exchange to daily transcript

Usage:
    python log_chat.py "Scott message" "Aimee response"
    
Or from Python:
    from log_chat import log_exchange
    log_exchange("Scott message", "Aimee response")
"""

import sys
import os
from datetime import datetime

def get_conversation_file():
    """Get today's conversation file path."""
    today = datetime.now().strftime("%Y-%m-%d")
    base_dir = "/root/.openclaw/workspace/memory/conversations"
    
    # Find the conversation file for today
    for filename in os.listdir(base_dir):
        if filename.startswith(today) and filename.endswith(".md"):
            return os.path.join(base_dir, filename)
    
    # If no file exists, create one
    return os.path.join(base_dir, f"{today}_conversation.md")

def get_next_message_number(filepath):
    """Get the next message number by counting existing messages."""
    if not os.path.exists(filepath):
        return 1
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Count existing message headers
    count = content.count("## Message ")
    return count + 1

def log_exchange(scott_msg, aimee_msg, timestamp=None):
    """
    Log a conversation exchange to the daily transcript.
    
    Args:
        scott_msg: Scott's message text
        aimee_msg: Aimee's response text
        timestamp: Optional datetime object (defaults to now)
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    filepath = get_conversation_file()
    msg_num = get_next_message_number(filepath)
    time_str = timestamp.strftime("%H:%M UTC")
    
    # Format the exchange
    exchange = f"""## Message {msg_num} - {time_str}
**Scott:** {scott_msg}

**Aimee:** {aimee_msg}

---

"""
    
    # Read existing content
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()
    else:
        content = f"# Conversation Transcript - {timestamp.strftime('%Y-%m-%d')}\n\n"
    
    # Remove the "Transcript ends here" line if it exists
    content = content.replace("\n---\n\n*Transcript ends here. Session ongoing.*", "")
    
    # Append new exchange
    content = content.rstrip() + "\n\n" + exchange + "*Transcript ends here. Session ongoing.*"
    
    # Write back
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✓ Logged message {msg_num} to {os.path.basename(filepath)}")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python log_chat.py 'Scott message' 'Aimee response'")
        sys.exit(1)
    
    scott_msg = sys.argv[1]
    aimee_msg = sys.argv[2]
    
    log_exchange(scott_msg, aimee_msg)
