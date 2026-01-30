#!/usr/bin/env python3
"""
Test different clustering thresholds to find optimal cluster count.
Runs clustering with multiple thresholds and shows statistics.
"""

import json
from pathlib import Path
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances

INPUT_FILE = Path("data/sab_messages_normalized.jsonl")

def load_messages():
    """Load normalized messages."""
    messages = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            messages.append(json.loads(line))
    return messages

def exact_grouping(messages):
    """Group messages by exact skeleton match."""
    skeleton_groups = defaultdict(list)
    for msg in messages:
        skeleton = msg['text_skeleton']
        skeleton_groups[skeleton].append(msg)
    return dict(skeleton_groups)

def cluster_at_threshold(skeleton_groups, threshold):
    """Cluster skeletons at given threshold."""
    skeletons = list(skeleton_groups.keys())
    
    if len(skeletons) <= 1:
        return {0: sum(skeleton_groups.values(), [])}
    
    # TF-IDF vectorization
    vectorizer = TfidfVectorizer(
        analyzer='char',
        ngram_range=(3, 5),
        min_df=1,
        lowercase=True
    )
    
    tfidf_matrix = vectorizer.fit_transform(skeletons)
    distance_matrix = cosine_distances(tfidf_matrix)
    
    # Clustering
    clustering = AgglomerativeClustering(
        n_clusters=None,
        metric='precomputed',
        linkage='average',
        distance_threshold=threshold
    )
    
    cluster_labels = clustering.fit_predict(distance_matrix)
    
    # Build final clusters
    final_clusters = defaultdict(list)
    for skeleton, label in zip(skeletons, cluster_labels):
        final_clusters[int(label)].extend(skeleton_groups[skeleton])
    
    return dict(final_clusters)

def print_stats(threshold, clusters, total_messages):
    """Print statistics for a clustering result."""
    cluster_sizes = [len(msgs) for msgs in clusters.values()]
    
    print(f"\nThreshold: {threshold:.2f}")
    print(f"  Clusters: {len(clusters)}")
    print(f"  Avg size: {np.mean(cluster_sizes):.1f}")
    print(f"  Median size: {np.median(cluster_sizes):.0f}")
    print(f"  Min: {min(cluster_sizes)}, Max: {max(cluster_sizes)}")
    print(f"  Top 5 cluster sizes: {sorted(cluster_sizes, reverse=True)[:5]}")

def main():
    print("Loading messages...")
    messages = load_messages()
    total = len(messages)
    print(f"Total messages: {total}")
    
    print("\nPass A: Exact skeleton grouping...")
    skeleton_groups = exact_grouping(messages)
    print(f"Unique skeletons: {len(skeleton_groups)}")
    
    print("\n" + "=" * 80)
    print("TESTING DIFFERENT THRESHOLDS")
    print("=" * 80)
    
    # Test different thresholds (higher values = fewer, larger clusters)
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
    
    results = []
    for threshold in thresholds:
        clusters = cluster_at_threshold(skeleton_groups, threshold)
        print_stats(threshold, clusters, total)
        results.append((threshold, len(clusters)))
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\nThreshold vs Cluster Count:")
    for threshold, count in results:
        print(f"  {threshold:.2f} → {count:3d} clusters")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    # Find threshold that gives closest to target range (20-60)
    target_range = (20, 60)
    best_threshold = None
    best_diff = float('inf')
    
    for threshold, count in results:
        if target_range[0] <= count <= target_range[1]:
            diff = abs(count - 40)  # Target middle of range
            if diff < best_diff:
                best_diff = diff
                best_threshold = threshold
    
    if best_threshold:
        print(f"\n✓ Recommended threshold: {best_threshold:.2f}")
        print(f"  (Produces {[c for t, c in results if t == best_threshold][0]} clusters)")
    else:
        # Find closest to range
        for threshold, count in results:
            if count < target_range[0]:
                continue
            print(f"\n✓ Recommended threshold: {threshold:.2f}")
            print(f"  (Produces {count} clusters)")
            break
    
    print(f"\nTo use this threshold, edit scripts/cluster.py line 20:")
    print(f"  SIMILARITY_THRESHOLD = {best_threshold if best_threshold else 0.5}")

if __name__ == '__main__':
    main()
