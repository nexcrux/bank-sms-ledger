#!/usr/bin/env python3
"""
Two-pass clustering of SAB messages:
  Pass A: Exact grouping by text_skeleton
  Pass B: Merge similar skeletons using TF-IDF + Agglomerative Clustering
"""

import json
import csv
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances

INPUT_FILE = Path("data/sab_messages_normalized.jsonl")
OUT_DIR = Path("out")
CLUSTERS_CSV = OUT_DIR / "clusters.csv"
MEMBERSHIP_CSV = OUT_DIR / "cluster_membership.csv"
EXAMPLES_DIR = OUT_DIR / "cluster_examples"

# Tunable parameters
SIMILARITY_THRESHOLD = 0.3  # Lower = more similar required (cosine distance)
MIN_CLUSTER_SIZE = 1  # Keep even single-message clusters

def load_messages() -> List[Dict]:
    """Load normalized messages."""
    messages = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            messages.append(json.loads(line))
    return messages

def pass_a_exact_grouping(messages: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Pass A: Group messages by exact text_skeleton match.
    Returns: dict mapping skeleton -> list of messages
    """
    skeleton_groups = defaultdict(list)
    for msg in messages:
        skeleton = msg['text_skeleton']
        skeleton_groups[skeleton].append(msg)
    return dict(skeleton_groups)

def pass_b_merge_similar(skeleton_groups: Dict[str, List[Dict]], threshold: float) -> Dict[int, List[Dict]]:
    """
    Pass B: Merge similar skeletons using TF-IDF + Agglomerative Clustering.
    Returns: dict mapping cluster_id -> list of messages
    """
    skeletons = list(skeleton_groups.keys())
    
    if len(skeletons) <= 1:
        # Only one skeleton, no merging needed
        return {0: sum(skeleton_groups.values(), [])}
    
    print(f"Pass B: Clustering {len(skeletons)} unique skeletons...")
    
    # Character n-gram TF-IDF (3-5 grams)
    vectorizer = TfidfVectorizer(
        analyzer='char',
        ngram_range=(3, 5),
        min_df=1,
        lowercase=True
    )
    
    tfidf_matrix = vectorizer.fit_transform(skeletons)
    
    # Compute cosine distance matrix
    distance_matrix = cosine_distances(tfidf_matrix)
    
    # Agglomerative clustering with distance threshold
    clustering = AgglomerativeClustering(
        n_clusters=None,
        metric='precomputed',
        linkage='average',
        distance_threshold=threshold
    )
    
    cluster_labels = clustering.fit_predict(distance_matrix)
    
    print(f"Pass B: Merged into {len(set(cluster_labels))} clusters")
    
    # Build final clusters
    final_clusters = defaultdict(list)
    for skeleton, label in zip(skeletons, cluster_labels):
        final_clusters[int(label)].extend(skeleton_groups[skeleton])
    
    return dict(final_clusters)

def get_top_tfidf_terms(messages: List[Dict], n_terms: int = 10) -> List[Tuple[str, float]]:
    """
    Extract top TF-IDF terms for a cluster.
    Uses text_norm for better term extraction.
    """
    texts = [msg['text_norm'] for msg in messages]
    
    if not texts:
        return []
    
    try:
        vectorizer = TfidfVectorizer(
            analyzer='word',
            token_pattern=r'(?u)\b\w+\b',
            max_features=100,
            min_df=1
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        # Sum TF-IDF scores across all documents in cluster
        feature_scores = np.asarray(tfidf_matrix.sum(axis=0)).flatten()
        feature_names = vectorizer.get_feature_names_out()
        
        # Sort by score
        top_indices = feature_scores.argsort()[-n_terms:][::-1]
        top_terms = [(feature_names[i], feature_scores[i]) for i in top_indices]
        
        return top_terms
    except Exception as e:
        print(f"Warning: Could not extract TF-IDF terms: {e}")
        return []

def write_cluster_outputs(clusters: Dict[int, List[Dict]]):
    """Write all cluster output files."""
    
    # Sort clusters by size (descending)
    sorted_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)
    
    # Ensure output directories exist
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Write clusters.csv
    with open(CLUSTERS_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['cluster_id', 'count', 'representative_id', 'representative_text_raw'])
        
        for cluster_id, messages in sorted_clusters:
            count = len(messages)
            rep_msg = messages[0]  # First message as representative
            writer.writerow([
                cluster_id,
                count,
                rep_msg['id'],
                rep_msg['text_raw']
            ])
    
    print(f"✓ Written: {CLUSTERS_CSV}")
    
    # 2. Write cluster_membership.csv
    with open(MEMBERSHIP_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'cluster_id'])
        
        for cluster_id, messages in clusters.items():
            for msg in messages:
                writer.writerow([msg['id'], cluster_id])
    
    print(f"✓ Written: {MEMBERSHIP_CSV}")
    
    # 3. Write cluster example files
    for cluster_id, messages in sorted_clusters:
        example_file = EXAMPLES_DIR / f"cluster_{cluster_id}.txt"
        
        with open(example_file, 'w', encoding='utf-8') as f:
            f.write(f"Cluster {cluster_id}\n")
            f.write(f"Count: {len(messages)}\n")
            f.write("=" * 80 + "\n\n")
            
            # Representative skeleton
            skeleton = messages[0]['text_skeleton']
            f.write(f"SKELETON:\n{skeleton}\n\n")
            f.write("=" * 80 + "\n\n")
            
            # Show up to 10 raw message examples
            f.write("RAW MESSAGE EXAMPLES (up to 10):\n\n")
            for i, msg in enumerate(messages[:10], 1):
                f.write(f"Example {i} (ID: {msg['id']}):\n")
                f.write(f"{msg['text_raw']}\n\n")
            
            f.write("=" * 80 + "\n\n")
            
            # Show up to 10 skeleton examples
            f.write("SKELETON EXAMPLES (up to 10):\n\n")
            for i, msg in enumerate(messages[:10], 1):
                f.write(f"{i}. {msg['text_skeleton']}\n")
            
            f.write("\n" + "=" * 80 + "\n\n")
            
            # Top TF-IDF terms
            f.write("TOP DISTINGUISHING TERMS:\n\n")
            top_terms = get_top_tfidf_terms(messages, n_terms=15)
            for term, score in top_terms:
                f.write(f"  {term}: {score:.4f}\n")
    
    print(f"✓ Written {len(clusters)} cluster example files to: {EXAMPLES_DIR}/")

def print_statistics(messages: List[Dict], clusters: Dict[int, List[Dict]]):
    """Print clustering statistics."""
    total = len(messages)
    num_clusters = len(clusters)
    
    cluster_sizes = [len(msgs) for msgs in clusters.values()]
    
    print("\n" + "=" * 80)
    print("CLUSTERING STATISTICS")
    print("=" * 80)
    print(f"Total messages:     {total}")
    print(f"Number of clusters: {num_clusters}")
    print(f"Avg cluster size:   {np.mean(cluster_sizes):.1f}")
    print(f"Median cluster size: {np.median(cluster_sizes):.0f}")
    print(f"Min cluster size:   {min(cluster_sizes)}")
    print(f"Max cluster size:   {max(cluster_sizes)}")
    
    # Cluster size distribution
    size_dist = Counter(cluster_sizes)
    print(f"\nCluster size distribution:")
    for size in sorted(size_dist.keys()):
        print(f"  Size {size}: {size_dist[size]} clusters")
    
    print("=" * 80 + "\n")

def main():
    print(f"Reading normalized messages from: {INPUT_FILE}")
    
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}. Run normalize.py first.")
    
    messages = load_messages()
    print(f"Loaded {len(messages)} messages\n")
    
    # Pass A: Exact skeleton grouping
    print("Pass A: Exact skeleton grouping...")
    skeleton_groups = pass_a_exact_grouping(messages)
    print(f"Pass A: Found {len(skeleton_groups)} unique skeletons\n")
    
    # Pass B: Merge similar skeletons
    clusters = pass_b_merge_similar(skeleton_groups, SIMILARITY_THRESHOLD)
    
    # Filter small clusters if needed
    if MIN_CLUSTER_SIZE > 1:
        clusters = {cid: msgs for cid, msgs in clusters.items() if len(msgs) >= MIN_CLUSTER_SIZE}
        print(f"After filtering (min_size={MIN_CLUSTER_SIZE}): {len(clusters)} clusters\n")
    
    # Write outputs
    write_cluster_outputs(clusters)
    
    # Print statistics
    print_statistics(messages, clusters)
    
    print("✓ Clustering complete!")
    print(f"\nOutputs written to:")
    print(f"  - {CLUSTERS_CSV}")
    print(f"  - {MEMBERSHIP_CSV}")
    print(f"  - {EXAMPLES_DIR}/")

if __name__ == '__main__':
    main()
