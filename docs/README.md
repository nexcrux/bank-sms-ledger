# Documentation

## Template Discovery Pipeline

The SAB SMS Template Discovery Pipeline analyzes bank SMS messages to automatically discover message templates through clustering.

**Start here:**
- [Quick Start](template_discovery/README.md) - Get started quickly
- [Full Guide](template_discovery/GUIDE.md) - Complete technical documentation
- [Results & Tuning](template_discovery/RESULTS.md) - Analysis and optimization
- [Project Summary](template_discovery/SUMMARY.md) - Comprehensive overview

## Cloudflare Worker

Documentation for the SMS banking transaction processing system using Cloudflare Workers and D1 database.

- [iOS Shortcuts Setup](cloudflare/SHORTCUT_SETUP.md) - Automatic SMS forwarding from iPhone
- [Database Queries](cloudflare/DATABASE_QUERIES.md) - Common D1 queries
- [Screenshots](cloudflare/screenshots/) - Setup screenshots

## Quick Links

**Template Discovery:**
```bash
# Run the pipeline
./scripts/run_pipeline.sh

# Tune clustering
python3 scripts/tune_clustering.py
```

**Cloudflare Worker:**
```bash
# Deploy
npm run deploy

# Query database
wrangler d1 execute sms-banking-db --command "SELECT * FROM raw_sms"
```
