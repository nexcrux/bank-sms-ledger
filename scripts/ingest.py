#!/usr/bin/env python3
"""
Ingest script for SAB SMS messages from iMessage export.
Parses the text file, filters SAB messages, and outputs canonical JSONL.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

INPUT_FILE = Path("/Users/abdullah/Desktop/imessage_export_SAB/SAB.txt")
OUTPUT_FILE = Path("data/sab_messages.jsonl")

def parse_imessage_export(file_path: Path) -> List[Dict]:
    """
    Parse iMessage export format.
    Format:
        <timestamp line>
        <sender>
        <message body line 1>
        <message body line 2>
        ...
        <blank line>
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    messages = []
    # Split by double newlines (message separator)
    raw_blocks = content.split('\n\n')
    
    message_id = 1
    for block in raw_blocks:
        if not block.strip():
            continue
        
        lines = block.strip().split('\n')
        if len(lines) < 2:
            continue
        
        # First line is timestamp
        timestamp_line = lines[0]
        # Extract the timestamp part before the parenthesis
        timestamp_match = re.match(r'^(.+?)(?:\s+\(|$)', timestamp_line)
        if not timestamp_match:
            continue
        
        timestamp_str = timestamp_match.group(1).strip()
        
        # Second line should be sender
        sender = lines[1].strip()
        
        # Remaining lines are the message body
        message_lines = lines[2:] if len(lines) > 2 else []
        message_text = '\n'.join(message_lines).strip()
        
        # Parse timestamp
        try:
            # Try multiple timestamp formats
            for fmt in [
                '%b %d, %Y %I:%M:%S %p',
                '%b %d, %Y  %I:%M:%S %p',  # Double space
            ]:
                try:
                    received_at = datetime.strptime(timestamp_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                # If no format matched, use current time as fallback
                received_at = datetime.now()
        except Exception:
            received_at = datetime.now()
        
        messages.append({
            'id': f'msg_{message_id:06d}',
            'sender': sender,
            'received_at': received_at.isoformat(),
            'text_raw': message_text
        })
        message_id += 1
    
    return messages

def filter_sab_messages(messages: List[Dict]) -> List[Dict]:
    """Filter messages where sender is 'SAB' (case insensitive)."""
    return [msg for msg in messages if msg['sender'].upper() == 'SAB']

def main():
    print(f"Reading dataset from: {INPUT_FILE}")
    
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Dataset file not found: {INPUT_FILE}")
    
    # Parse all messages
    all_messages = parse_imessage_export(INPUT_FILE)
    print(f"Total messages parsed: {len(all_messages)}")
    
    # Filter SAB messages
    sab_messages = filter_sab_messages(all_messages)
    print(f"SAB messages filtered: {len(sab_messages)}")
    
    if len(sab_messages) == 0:
        raise ValueError("ERROR: Zero SAB messages found in dataset!")
    
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to JSONL
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for msg in sab_messages:
            f.write(json.dumps(msg, ensure_ascii=False) + '\n')
    
    print(f"✓ Written {len(sab_messages)} messages to: {OUTPUT_FILE}")
    
    # Print sample statistics
    print("\n=== Sample Messages ===")
    for i, msg in enumerate(sab_messages[:3], 1):
        print(f"\nMessage {i}:")
        print(f"  ID: {msg['id']}")
        print(f"  Timestamp: {msg['received_at']}")
        print(f"  Text: {msg['text_raw'][:100]}...")

if __name__ == '__main__':
    main()
