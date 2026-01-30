# SMS Banking Ledger

SMS banking transaction processing system using Cloudflare Workers and D1 database.

## 🔬 SAB Template Discovery Pipeline

A data-driven clustering pipeline that automatically discovers message templates from SAB (Saudi Awwal Bank) SMS history.

### Quick Start

```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Run the full pipeline
./scripts/run_pipeline.sh
```

**Results from 1,668 messages:**
- 383 clusters discovered
- Templates at `templates/sab/*.yaml`
- Report at `out/cluster_report.md`

**Next:** Tune clustering threshold to merge similar templates

### Documentation
- [Quick Start](docs/template_discovery/) - Start here!
- [Full Guide](docs/template_discovery/GUIDE.md) - Complete pipeline documentation
- [Results & Tuning](docs/template_discovery/RESULTS.md) - Initial results and recommendations
- [Project Summary](docs/template_discovery/SUMMARY.md) - Comprehensive overview

---

## Project Status

### ✅ Completed
- **Issue #1**: Cloudflare Worker + D1 database infrastructure ✅
- **Bonus**: iOS Shortcuts automation for automatic SMS forwarding ✅

### 🚀 Live & Running
- **Production URL**: https://bank-sms-ledger.abdullah-915.workers.dev
- **Database**: D1 (EEUR region) - 4 SMS messages captured
- **Automation**: iPhone automatically forwarding all SMS to Cloudflare

### 📊 Progress
- Milestone 1 (Single Bank MVP): **1/5 complete (20%)**
  - ✅ Issue #1: D1 schema + basic Worker
  - 🔜 Issue #2: parsed_transactions table + bank parser
  - ⏳ Issue #3: Workflow orchestration
  - ⏳ Issue #4: ledger_entries table
  - ⏳ Issue #5: NAS export integration

### 🎯 Next Up
**Issue #2**: Add parsed_transactions table + single bank parser

## Prerequisites

- Node.js 18+ and npm
- Cloudflare account (free tier works)
- Wrangler CLI (installed via `npm install -g wrangler`)

## Setup Instructions

### 1. Authenticate with Cloudflare

```bash
wrangler login
```

This will open a browser window for authentication.

### 2. Create D1 Database

```bash
npm run db:create
```

This creates a new D1 database named `sms-banking-db`. Copy the `database_id` from the output and update `wrangler.toml`:

```toml
[[d1_databases]]
binding = "DB"
database_name = "sms-banking-db"
database_id = "YOUR_DATABASE_ID_HERE"  # Replace with actual ID
```

### 3. Initialize Database Schema

```bash
npm run db:init
```

This creates the `raw_sms` and `processing_state` tables.

### 4. Deploy to Cloudflare

```bash
npm run deploy
```

Your worker will be deployed and you'll receive a URL like `https://bank-sms-ledger.YOUR_SUBDOMAIN.workers.dev`

## Development

### Local Development

```bash
npm run dev
```

This starts a local development server at `http://localhost:8787`

### Testing the /ingest Endpoint

```bash
# Test SMS ingestion
curl -X POST http://localhost:8787/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "body": "Your transaction of SAR 150.00 at Starbucks has been processed.",
    "sender": "+966501234567",
    "received_at": "2024-01-28T12:00:00Z"
  }'

# Response (first time):
{
  "message": "SMS ingested successfully",
  "data": {
    "id": 1,
    "body": "Your transaction of SAR 150.00 at Starbucks has been processed.",
    "sender": "+966501234567",
    "received_at": "2024-01-28T12:00:00Z",
    "event_id": "a1b2c3d4e5f6g7h8",
    "created_at": "2024-01-28T12:00:01.000Z"
  }
}

# Test idempotency (same SMS again):
curl -X POST http://localhost:8787/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "body": "Your transaction of SAR 150.00 at Starbucks has been processed.",
    "sender": "+966501234567",
    "received_at": "2024-01-28T12:00:00Z"
  }'

# Response (duplicate):
{
  "message": "SMS already processed (duplicate)",
  "duplicate": true
}
```

### Query Database

```bash
# View all raw SMS
wrangler d1 execute sms-banking-db --command "SELECT * FROM raw_sms"

# View processing state
wrangler d1 execute sms-banking-db --command "SELECT * FROM processing_state"

# Count total SMS
wrangler d1 execute sms-banking-db --command "SELECT COUNT(*) as total FROM raw_sms"
```

## Project Structure

```
bank-sms-ledger/
├── src/
│   ├── index.ts              # Cloudflare Worker entry point
│   ├── db/
│   │   └── schema.sql        # D1 database schema
│   ├── stages/
│   │   └── ingest.ts         # SMS ingestion logic
│   ├── models/
│   │   └── raw-sms.ts        # TypeScript types
│   └── utils/
│       └── idempotency.ts    # Event ID generation
├── wrangler.toml             # Cloudflare Workers configuration
├── package.json
└── tsconfig.json
```

## iOS Shortcuts Automation (Bonus Feature!)

Automatically forward SMS from your iPhone to Cloudflare without any manual intervention.

### How It Works

```
📱 iPhone receives SMS
    ↓
🤖 Shortcuts automation triggers automatically
    ↓
📅 Formats timestamp to ISO 8601
    ↓
🌐 POSTs to Cloudflare /ingest endpoint
    ↓
💾 Saved to D1 database
    ↓
✅ Ready for parsing (Issue #2)
```

### Setup Guide

**Complete step-by-step instructions**: [`docs/cloudflare/SHORTCUT_SETUP.md`](docs/cloudflare/SHORTCUT_SETUP.md)

**Screenshots**: Available in `docs/cloudflare/screenshots/`

Key steps:
1. Create automation trigger (Message Contains " ")
2. Create "SMS Forwarding to Cloudflare" shortcut
3. Add Format Date action (ISO 8601)
4. Add HTTP POST to /ingest endpoint
5. Build JSON with: body, sender, received_at

### What Gets Captured

- **All SMS messages** are forwarded (filtering happens in parsing layer)
- Includes: message body, sender, timestamp
- Supports Arabic text
- Runs silently in background
- No user interaction needed

### Current Status

- ✅ Automation running on iPhone
- ✅ 4 SMS captured automatically
- ✅ ISO 8601 timestamp formatting
- ✅ Idempotency working

## Database Schema

### raw_sms Table

Immutable source of truth for all received SMS messages.

| Column       | Type    | Description                           |
|------------- |---------|---------------------------------------|
| id           | INTEGER | Primary key (auto-increment)          |
| body         | TEXT    | SMS text content                      |
| sender       | TEXT    | Phone number or sender ID             |
| received_at  | TEXT    | ISO 8601 timestamp                    |
| event_id     | TEXT    | Hash for idempotency (UNIQUE)         |
| created_at   | TEXT    | Record creation timestamp             |

### processing_state Table

Tracks cursor position for each processing stage.

| Column            | Type    | Description                      |
|------------------ |---------|----------------------------------|
| stage             | TEXT    | Primary key ('parse', 'ledger', 'export') |
| last_processed_id | INTEGER | Last processed raw_sms.id        |
| last_processed_at | TEXT    | Last processing timestamp        |

## Features Implemented (Issue #1)

✅ Cloudflare Workers project initialized
✅ D1 database schema defined
✅ POST /ingest endpoint for SMS ingestion
✅ Idempotency via event_id (SHA-256 hash)
✅ UNIQUE constraint prevents duplicate processing
✅ TypeScript with proper types
✅ Error handling and validation

## Next Steps

- **Issue #2**: Add `parsed_transactions` table + first bank parser
- **Issue #3**: Add Workflow orchestration
- **Issue #4**: Add `ledger_entries` table + promotion logic
- **Issue #5**: Add NAS export integration

## Acceptance Criteria Checklist

- [x] Cloudflare Workers project initialized with wrangler
- [x] D1 database schema created (raw_sms + processing_state)
- [x] POST /ingest endpoint accepts SMS and writes to raw_sms
- [ ] Worker deployed to Cloudflare (requires authentication)
- [ ] Can curl POST an SMS to deployed endpoint
- [ ] SMS appears in raw_sms table (can verify via wrangler d1 execute)
- [x] Posting same SMS twice results in only one row (idempotency implemented)

## Support

For issues or questions, see: https://github.com/nexcrux/bank-sms-ledger/issues
