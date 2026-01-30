# SAB SMS Template Discovery Pipeline

This pipeline performs data-driven template discovery on SAB (Saudi Awwal Bank) SMS messages using a two-pass clustering approach.

## Overview

The pipeline consists of 5 main scripts that run sequentially:

1. **ingest.py** - Parse iMessage export and filter SAB messages
2. **normalize.py** - Normalize text and create skeletons with placeholders
3. **cluster.py** - Two-pass clustering (exact + TF-IDF similarity)
4. **generate_report.py** - Create readable markdown report
5. **generate_templates.py** - Generate starter YAML template files

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt
```

## Usage

### Quick Start - Run Full Pipeline

```bash
# Run all steps in sequence
python scripts/ingest.py && \
python scripts/normalize.py && \
python scripts/cluster.py && \
python scripts/generate_report.py && \
python scripts/generate_templates.py
```

### Step-by-Step Execution

```bash
# Step 1: Ingest and filter SAB messages
python scripts/ingest.py

# Step 2: Normalize text and create skeletons
python scripts/normalize.py

# Step 3: Cluster messages into templates
python scripts/cluster.py

# Step 4: Generate human-readable report
python scripts/generate_report.py

# Step 5: Generate YAML template files
python scripts/generate_templates.py
```

## Output Files

After running the pipeline, you'll find:

### Data Files (Intermediate)
- `data/sab_messages.jsonl` - Canonical SAB messages
- `data/sab_messages_normalized.jsonl` - Normalized messages with skeletons

### Cluster Outputs
- `out/clusters.csv` - Cluster metadata (ID, count, representative message)
- `out/cluster_membership.csv` - Message to cluster mapping
- `out/cluster_examples/cluster_<id>.txt` - Detailed examples for each cluster
- `out/cluster_report.md` - Human-readable report sorted by cluster size

### Templates
- `templates/sab/template_<id>.yaml` - Starter template files for each cluster

## Tuning Clustering

The clustering behavior can be adjusted in `scripts/cluster.py`:

```python
# Line ~20-21 in cluster.py
SIMILARITY_THRESHOLD = 0.3  # Lower = more similar required (range: 0.0-1.0)
MIN_CLUSTER_SIZE = 1        # Minimum messages per cluster
```

### Adjusting SIMILARITY_THRESHOLD

- **Lower values (0.1-0.2)**: Stricter merging, more clusters, more granular templates
- **Default (0.3)**: Balanced merging
- **Higher values (0.4-0.6)**: Aggressive merging, fewer clusters, more generalized templates

After changing the threshold:
```bash
# Re-run clustering and downstream steps
python scripts/cluster.py && \
python scripts/generate_report.py && \
python scripts/generate_templates.py
```

## Adding New Data

To add new SAB messages:

1. Export new messages to the same iMessage export format
2. Append to or replace the input file at: `/Users/abdullah/Desktop/imessage_export_SAB/SAB.txt`
3. Re-run the full pipeline

The pipeline is idempotent - it will overwrite outputs deterministically.

## Normalization Rules

The normalize step applies these transformations:

1. **Arabic Indic digits** → Western digits (٠-٩ → 0-9)
2. **Whitespace** → Normalized to single spaces
3. **English text** → Lowercased (Arabic preserved)
4. **Diacritics & tatweel** → Removed

### Placeholder Replacements

Variable parts are replaced with placeholders in the skeleton:

| Pattern | Placeholder | Example |
|---------|-------------|---------|
| Money amounts | `<AMOUNT>` | SAR 40.00 → `<AMOUNT>` |
| Timestamps | `<DATETIME>` | 2025-01-23 15:36:03 → `<DATETIME>` |
| Dates | `<DATE>` | 2025-01-23 → `<DATE>` |
| Times | `<TIME>` | 15:36:03 → `<TIME>` |
| Masked accounts | `<ACCT>` | ***1300 → `<ACCT>` |
| IBANs | `<IBAN>` | SA*****8605 → `<IBAN>` |
| Reference numbers | `<REF>` | 20250123SASABB... → `<REF>` |
| OTP codes | `<CODE>` | 6620 → `<CODE>` |
| Generic numbers | `<NUM>` | 1234 → `<NUM>` |

## Clustering Algorithm

**Pass A: Exact Grouping**
- Group messages with identical skeletons
- Fast, deterministic
- Creates initial clusters

**Pass B: Similarity Merging**
- Uses character n-gram TF-IDF (3-5 grams)
- Agglomerative clustering with cosine distance
- Merges similar skeletons
- Configurable threshold

## Expected Results

With 1 year of SAB messages, expect:
- **20-60 clusters** (depending on threshold)
- **3-10 major templates** (login, purchase, transfer, OTP, balance)
- **10-40 minor templates** (specific transaction types, notifications)

## Next Steps

After template discovery:

1. Review `out/cluster_report.md` to understand message types
2. Examine `out/cluster_examples/` for detailed cluster analysis
3. Edit `templates/sab/template_*.yaml` files to:
   - Set correct `message_type` (purchase, transfer, otp, login, etc.)
   - Define field extraction patterns
   - Add validation rules
4. Build parsers using the template files
5. Create unit tests using example messages from clusters

## Troubleshooting

### Zero SAB messages found
- Check that input file exists at specified path
- Verify sender name is exactly "SAB" in the export
- Check file encoding (should be UTF-8)

### Too many/few clusters
- Adjust `SIMILARITY_THRESHOLD` in `scripts/cluster.py`
- Lower threshold → more clusters
- Higher threshold → fewer clusters

### Missing dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Memory issues with large datasets
- The pipeline uses efficient streaming for I/O
- Clustering loads full dataset into memory
- For >100k messages, consider batching or using Dask

## Technical Details

- **Language:** Python 3.8+
- **Key libraries:** scikit-learn, numpy, pyyaml
- **Clustering:** Agglomerative with cosine distance
- **Vectorization:** Character n-gram TF-IDF
- **Encoding:** UTF-8 throughout
- **Format:** JSONL for intermediate data, CSV for analysis, YAML for templates
