#!/usr/bin/env python3
"""
Normalize SAB messages for clustering.
Converts Arabic Indic digits, normalizes whitespace, replaces variable parts with placeholders.
"""

import json
import re
from pathlib import Path
from typing import Dict

INPUT_FILE = Path("data/sab_messages.jsonl")
OUTPUT_FILE = Path("data/sab_messages_normalized.jsonl")

# Arabic Indic digits to Western digits
ARABIC_INDIC_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')

# Common Arabic diacritics and tatweel
ARABIC_DIACRITICS = re.compile(r'[\u064B-\u065F\u0640]')

def normalize_text(text: str) -> str:
    """
    Normalize text for clustering while preserving structure.
    - Convert Arabic Indic digits to Western
    - Remove Arabic diacritics and tatweel
    - Normalize whitespace
    - Lowercase English text (preserve Arabic)
    """
    # Convert Arabic Indic digits
    text = text.translate(ARABIC_INDIC_DIGITS)
    
    # Remove Arabic diacritics and tatweel
    text = ARABIC_DIACRITICS.sub('', text)
    
    # Normalize whitespace (multiple spaces/tabs to single space)
    text = re.sub(r'[\t\r]+', ' ', text)
    text = re.sub(r' +', ' ', text)
    
    # Lowercase only English characters (preserve Arabic case)
    result = []
    for char in text:
        if 'A' <= char <= 'Z':
            result.append(char.lower())
        else:
            result.append(char)
    text = ''.join(result)
    
    return text.strip()

def create_skeleton(text_norm: str) -> str:
    """
    Create skeleton by replacing variable parts with placeholders.
    Order matters - process more specific patterns first.
    """
    skeleton = text_norm
    
    # 1. Replace money amounts (SAR X.XX or X.XX SAR)
    # Match patterns like: SAR 40.00, 1000.00 SAR, 40.00SAR
    skeleton = re.sub(r'\bsar\s*[\d,]+\.?\d*\b', '<AMOUNT>', skeleton, flags=re.IGNORECASE)
    skeleton = re.sub(r'\b[\d,]+\.?\d*\s*sar\b', '<AMOUNT>', skeleton, flags=re.IGNORECASE)
    skeleton = re.sub(r'\b[\d,]+\.\d{2}\b', '<AMOUNT>', skeleton)  # Catch remaining X.XX patterns
    
    # 2. Replace timestamps (YYYY-MM-DD HH:MM:SS or similar)
    skeleton = re.sub(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', '<DATETIME>', skeleton)
    
    # 3. Replace dates (YYYY-MM-DD or DD-MM-YYYY or similar)
    skeleton = re.sub(r'\d{4}-\d{2}-\d{2}', '<DATE>', skeleton)
    skeleton = re.sub(r'\d{2}/\d{2}/\d{4}', '<DATE>', skeleton)
    skeleton = re.sub(r'\d{2}-\d{2}-\d{4}', '<DATE>', skeleton)
    
    # 4. Replace times (HH:MM:SS or HH:MM)
    skeleton = re.sub(r'\d{2}:\d{2}:\d{2}', '<TIME>', skeleton)
    skeleton = re.sub(r'\d{2}:\d{2}', '<TIME>', skeleton)
    
    # 5. Replace long reference numbers (typically 15+ digits/chars)
    skeleton = re.sub(r'\b[a-z0-9]{15,}\b', '<REF>', skeleton, flags=re.IGNORECASE)
    
    # 6. Replace masked account/card numbers (***XXXX or *****XXXX)
    skeleton = re.sub(r'\*{3,}\d{4}', '<ACCT>', skeleton)
    
    # 7. Replace IBANs (pattern: SA followed by digits, possibly masked)
    skeleton = re.sub(r'\b\*{0,}sa\d{2}[a-z0-9*]{18,}\b', '<IBAN>', skeleton, flags=re.IGNORECASE)
    
    # 8. Replace standalone 4+ digit numbers (likely amounts, codes, or identifiers)
    skeleton = re.sub(r'\b\d{4,}\b', '<NUM>', skeleton)
    
    # 9. Replace 6-digit codes (OTP codes)
    skeleton = re.sub(r'\b\d{6}\b', '<CODE>', skeleton)
    
    # Normalize multiple consecutive placeholders of same type
    skeleton = re.sub(r'(<AMOUNT>\s*){2,}', '<AMOUNT>', skeleton)
    skeleton = re.sub(r'(<NUM>\s*){2,}', '<NUM>', skeleton)
    
    return skeleton.strip()

def main():
    print(f"Reading messages from: {INPUT_FILE}")
    
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}. Run ingest.py first.")
    
    messages = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            messages.append(json.loads(line))
    
    print(f"Loaded {len(messages)} messages")
    
    # Normalize each message
    normalized_count = 0
    for msg in messages:
        text_raw = msg['text_raw']
        text_norm = normalize_text(text_raw)
        text_skeleton = create_skeleton(text_norm)
        
        msg['text_norm'] = text_norm
        msg['text_skeleton'] = text_skeleton
        normalized_count += 1
    
    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for msg in messages:
            f.write(json.dumps(msg, ensure_ascii=False) + '\n')
    
    print(f"✓ Normalized {normalized_count} messages")
    print(f"✓ Written to: {OUTPUT_FILE}")
    
    # Show examples
    print("\n=== Normalization Examples ===")
    for i, msg in enumerate(messages[:3], 1):
        print(f"\nExample {i}:")
        print(f"  Raw:      {msg['text_raw'][:80]}...")
        print(f"  Norm:     {msg['text_norm'][:80]}...")
        print(f"  Skeleton: {msg['text_skeleton'][:80]}...")

if __name__ == '__main__':
    main()
