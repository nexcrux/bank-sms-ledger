#!/bin/bash
# Master script to run the full SAB template discovery pipeline

set -e  # Exit on any error

echo "======================================"
echo "SAB SMS Template Discovery Pipeline"
echo "======================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found. Please install Python 3.8+."
    exit 1
fi

# Check if dependencies are installed
echo "Checking dependencies..."
python3 -c "import sklearn, numpy, yaml" 2>/dev/null || {
    echo "Installing dependencies..."
    pip install -r requirements.txt
}

echo ""
echo "Step 1/5: Ingesting SAB messages..."
python3 scripts/ingest.py
echo ""

echo "Step 2/5: Normalizing text..."
python3 scripts/normalize.py
echo ""

echo "Step 3/5: Clustering messages..."
python3 scripts/cluster.py
echo ""

echo "Step 4/5: Generating report..."
python3 scripts/generate_report.py
echo ""

echo "Step 5/5: Generating template files..."
python3 scripts/generate_templates.py
echo ""

echo "======================================"
echo "Pipeline Complete!"
echo "======================================"
echo ""
echo "Outputs:"
echo "  - Data: data/sab_messages*.jsonl"
echo "  - Clusters: out/clusters.csv, out/cluster_membership.csv"
echo "  - Examples: out/cluster_examples/"
echo "  - Report: out/cluster_report.md"
echo "  - Templates: templates/sab/"
echo ""
echo "Next: Review out/cluster_report.md"
