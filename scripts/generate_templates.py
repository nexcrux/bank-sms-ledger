#!/usr/bin/env python3
"""
Generate starter YAML template files for each cluster.
"""

import json
import csv
import yaml
from pathlib import Path
from collections import defaultdict
import re

INPUT_FILE = Path("data/sab_messages_normalized.jsonl")
CLUSTERS_CSV = Path("out/clusters.csv")
MEMBERSHIP_CSV = Path("out/cluster_membership.csv")
TEMPLATES_DIR = Path("templates/sab")

def load_messages() -> dict:
    """Load messages indexed by ID."""
    messages = {}
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            msg = json.loads(line)
            messages[msg['id']] = msg
    return messages

def load_clusters() -> list:
    """Load cluster metadata."""
    clusters = []
    with open(CLUSTERS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            clusters.append({
                'cluster_id': int(row['cluster_id']),
                'count': int(row['count']),
                'representative_id': row['representative_id']
            })
    return clusters

def load_membership() -> dict:
    """Load cluster membership mapping."""
    membership = defaultdict(list)
    with open(MEMBERSHIP_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cluster_id = int(row['cluster_id'])
            msg_id = row['id']
            membership[cluster_id].append(msg_id)
    return dict(membership)

def detect_language(text: str) -> str:
    """
    Detect primary language based on Unicode ranges.
    Arabic: U+0600 to U+06FF
    """
    arabic_count = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    english_count = sum(1 for c in text if c.isalpha() and c.isascii())
    total_alpha = arabic_count + english_count
    
    if total_alpha == 0:
        return 'unknown'
    
    arabic_ratio = arabic_count / total_alpha
    english_ratio = english_count / total_alpha
    
    if arabic_ratio > 0.7:
        return 'ar'
    elif english_ratio > 0.7:
        return 'en'
    else:
        return 'mixed'

def detect_fields_from_skeleton(skeleton: str) -> dict:
    """
    Detect required and optional fields based on placeholders.
    Returns dict with 'required' and 'optional' lists.
    """
    required = []
    optional = []
    
    # Fields that appear in placeholders
    if '<AMOUNT>' in skeleton:
        required.append('amount')
    if '<DATE>' in skeleton or '<DATETIME>' in skeleton:
        required.append('date')
    if '<TIME>' in skeleton or '<DATETIME>' in skeleton:
        required.append('time')
    if '<ACCT>' in skeleton:
        required.append('account_masked')
    if '<IBAN>' in skeleton:
        required.append('iban')
    if '<CODE>' in skeleton:
        required.append('otp_code')
    if '<REF>' in skeleton:
        required.append('reference_number')
    
    # Check for common optional fields
    skeleton_lower = skeleton.lower()
    if 'balance' in skeleton_lower or 'الرصيد' in skeleton or 'رصيد' in skeleton:
        optional.append('balance')
    
    if 'لدى' in skeleton or 'merchant' in skeleton_lower:
        optional.append('merchant_name')
    
    if 'الرسوم' in skeleton or 'fee' in skeleton_lower:
        optional.append('fee')
    
    return {
        'required': required,
        'optional': optional
    }

def generate_parse_notes(skeleton: str, messages: list) -> str:
    """Generate parse notes based on skeleton and sample messages."""
    notes = []
    
    # Identify transaction types
    skeleton_lower = skeleton.lower()
    text_samples = ' '.join([m['text_raw'] for m in messages[:3]]).lower()
    
    if 'شراء' in skeleton or 'purchase' in skeleton_lower:
        notes.append("Transaction type: Purchase (POS or online)")
    if 'حوالة' in skeleton or 'transfer' in skeleton_lower:
        notes.append("Transaction type: Transfer")
    if 'سحب' in skeleton or 'withdrawal' in skeleton_lower:
        notes.append("Transaction type: Withdrawal")
    if 'logged in' in skeleton_lower or 'login' in skeleton_lower:
        notes.append("Message type: Login notification")
    if 'otp' in skeleton_lower or 'كلمة مرور' in skeleton:
        notes.append("Message type: OTP/Authentication code")
    
    # Mention specific fields to extract
    if '<AMOUNT>' in skeleton:
        notes.append("Extract amount value and currency")
    if '<ACCT>' in skeleton:
        notes.append("Extract masked account/card number")
    if '<DATETIME>' in skeleton or '<DATE>' in skeleton:
        notes.append("Parse transaction timestamp")
    if 'لدى' in skeleton:
        notes.append("Extract merchant name (after 'لدى' keyword)")
    if '<REF>' in skeleton:
        notes.append("Extract reference/transaction ID")
    
    return ' | '.join(notes) if notes else 'Review skeleton for extractable patterns'

def generate_templates(messages: dict, clusters: list, membership: dict):
    """Generate YAML template files for each cluster."""
    
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    
    for cluster_info in clusters:
        cluster_id = cluster_info['cluster_id']
        count = cluster_info['count']
        
        # Get messages in this cluster
        msg_ids = membership.get(cluster_id, [])
        cluster_messages = [messages[mid] for mid in msg_ids[:10]]  # Sample up to 10
        
        if not cluster_messages:
            continue
        
        # Get skeleton
        skeleton = cluster_messages[0]['text_skeleton']
        
        # Detect language
        sample_text = cluster_messages[0]['text_raw']
        language = detect_language(sample_text)
        
        # Detect fields
        fields = detect_fields_from_skeleton(skeleton)
        
        # Generate parse notes
        parse_notes = generate_parse_notes(skeleton, cluster_messages)
        
        # Create template structure
        template = {
            'id': f'SAB_{cluster_id:03d}',
            'message_type': 'unknown',  # To be filled manually
            'language': language,
            'skeleton': skeleton,
            'required_fields': fields['required'],
            'optional_fields': fields['optional'],
            'parse_notes': parse_notes,
            'cluster_info': {
                'cluster_id': cluster_id,
                'message_count': count,
                'sample_messages': [msg['text_raw'] for msg in cluster_messages[:3]]
            }
        }
        
        # Write YAML file
        template_file = TEMPLATES_DIR / f"template_{cluster_id:03d}.yaml"
        with open(template_file, 'w', encoding='utf-8') as f:
            yaml.dump(template, f, allow_unicode=True, sort_keys=False, default_flow_style=False, width=120)
    
    print(f"✓ Generated {len(clusters)} template files in: {TEMPLATES_DIR}/")

def main():
    print("Generating template files...")
    
    messages = load_messages()
    clusters = load_clusters()
    membership = load_membership()
    
    generate_templates(messages, clusters, membership)
    
    print("\n✓ Template generation complete!")

if __name__ == '__main__':
    main()
