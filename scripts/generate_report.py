#!/usr/bin/env python3
"""
Generate a readable markdown report of clusters sorted by size.
"""

import json
import csv
from pathlib import Path
from collections import defaultdict
import re

INPUT_FILE = Path("data/sab_messages_normalized.jsonl")
CLUSTERS_CSV = Path("out/clusters.csv")
MEMBERSHIP_CSV = Path("out/cluster_membership.csv")
REPORT_FILE = Path("out/cluster_report.md")

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
                'representative_id': row['representative_id'],
                'representative_text_raw': row['representative_text_raw']
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

def detect_fields(skeleton: str) -> list:
    """Detect which fields are present based on placeholders."""
    fields = []
    if '<AMOUNT>' in skeleton:
        fields.append('amount')
    if '<DATE>' in skeleton or '<DATETIME>' in skeleton:
        fields.append('date')
    if '<TIME>' in skeleton or '<DATETIME>' in skeleton:
        fields.append('time')
    if '<ACCT>' in skeleton:
        fields.append('account')
    if '<IBAN>' in skeleton:
        fields.append('iban')
    if '<CODE>' in skeleton:
        fields.append('code/otp')
    if '<REF>' in skeleton:
        fields.append('reference')
    if '<NUM>' in skeleton:
        fields.append('numeric_id')
    
    # Detect balance by looking for common Arabic/English terms
    skeleton_lower = skeleton.lower()
    if 'balance' in skeleton_lower or 'الرصيد' in skeleton or 'رصيد' in skeleton:
        fields.append('balance')
    
    # Detect merchant
    if 'لدى' in skeleton or 'merchant' in skeleton_lower:
        fields.append('merchant')
    
    return fields

def generate_report(messages: dict, clusters: list, membership: dict):
    """Generate the markdown report."""
    
    total_messages = sum(c['count'] for c in clusters)
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("# SAB SMS Template Discovery Report\n\n")
        f.write(f"**Generated:** {Path.cwd()}\n\n")
        f.write(f"**Total Messages:** {total_messages:,}\n")
        f.write(f"**Total Clusters:** {len(clusters)}\n\n")
        f.write("---\n\n")
        
        # Sort clusters by count (descending)
        sorted_clusters = sorted(clusters, key=lambda x: x['count'], reverse=True)
        
        for rank, cluster in enumerate(sorted_clusters, 1):
            cluster_id = cluster['cluster_id']
            count = cluster['count']
            percent = (count / total_messages) * 100
            
            # Get all messages in this cluster
            msg_ids = membership.get(cluster_id, [])
            cluster_messages = [messages[mid] for mid in msg_ids[:5]]  # Get up to 5 examples
            
            # Get skeleton from first message
            skeleton = cluster_messages[0]['text_skeleton'] if cluster_messages else "N/A"
            
            # Detect fields
            fields = detect_fields(skeleton)
            
            f.write(f"## Cluster {cluster_id} (Rank #{rank})\n\n")
            f.write(f"- **Count:** {count:,} messages ({percent:.1f}%)\n")
            f.write(f"- **Detected Fields:** {', '.join(fields) if fields else 'none'}\n\n")
            
            f.write(f"### Skeleton\n\n")
            f.write(f"```\n{skeleton}\n```\n\n")
            
            f.write(f"### Representative Messages (showing up to 3)\n\n")
            for i, msg in enumerate(cluster_messages[:3], 1):
                f.write(f"**Example {i}:**\n\n")
                f.write(f"```\n{msg['text_raw']}\n```\n\n")
            
            f.write("---\n\n")
    
    print(f"✓ Generated report: {REPORT_FILE}")

def main():
    print("Generating cluster report...")
    
    messages = load_messages()
    clusters = load_clusters()
    membership = load_membership()
    
    generate_report(messages, clusters, membership)
    
    print("\n✓ Report generation complete!")

if __name__ == '__main__':
    main()
