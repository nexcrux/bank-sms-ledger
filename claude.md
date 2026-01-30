# SMS Banking System - Build Instructions

## 🎯 Current Status (Jan 30, 2026)

### ✅ What's Been Completed

**Issue #1: Infrastructure (DONE)**
- ✅ Cloudflare Workers project initialized
- ✅ D1 database created (ID: 8e45ca34-1aed-47cc-b4d5-c1472ab5172b)
- ✅ Database schema deployed (`raw_sms` + `processing_state` tables)
- ✅ POST /ingest endpoint deployed and working
- ✅ Idempotency implemented (SHA-256 event_id)
- ✅ Production URL: https://bank-sms-ledger.abdullah-915.workers.dev

**Bonus: iOS Shortcuts Automation (DONE)**
- ✅ Automatic SMS forwarding from iPhone to Cloudflare
- ✅ Triggers on ALL incoming SMS (filtering happens in parse layer)
- ✅ ISO 8601 timestamp formatting
- ✅ No manual intervention needed
- ✅ Documentation: `docs/SHORTCUT_SETUP.md`
- ✅ Screenshots: `docs/screenshots/`

**Current Database Status:**
- 4 SMS messages captured (2 manual tests + 2 automatic from iPhone)
- Handles Arabic text correctly
- Idempotency working
- Ready for parsing (Issue #2)

### 🔜 Next Up: Issue #2

**Add parsed_transactions table + single bank parser**

Will need from user:
- Real bank SMS examples from primary Saudi bank
- Bank's SMS sender ID/pattern
- Fields to extract: amount, merchant, date, card digits, transaction type

### 📊 Progress

- **Milestone 1** (Single Bank MVP): 1/5 complete (20%)
  - ✅ Issue #1: D1 schema + basic Worker
  - 🔜 Issue #2: parsed_transactions table + bank parser
  - ⏳ Issue #3: Workflow orchestration
  - ⏳ Issue #4: ledger_entries table
  - ⏳ Issue #5: NAS export integration

## Context: What We've Already Decided

### Architecture Choice
We're using **Grok's Workflow orchestration with Claude's separate tables approach**:

- **Data Model:** 4 separate D1 tables (immutable source → projections)
  - `raw_sms` - immutable SMS as received, never modified
  - `parsed_transactions` - extracted fields, references raw_sms_id
  - `ledger_entries` - canonical ledger format, references parsed_transaction_id
  - `exports` - export log tracking what was sent where, references ledger_entry_id

- **Orchestration:** Cloudflare Workflows (not manual HTTP endpoints)
  - One Workflow with 4 sequential steps
  - Built-in retry logic and state persistence
  - Auto-retry on failures with exponential backoff

- **Progress Tracking:** Cursor-based via `processing_state` table
  - Tracks last processed ID per stage (parse, ledger, export)
  - Enables safe replays and idempotent reruns

### Repo Structure (From Claude's Response)
```
sms-banking/
├── src/
│   ├── index.ts                 # Cloudflare Worker entry point
│   ├── workflows/
│   │   └── sms-processing.ts    # Main workflow orchestration
│   ├── db/
│   │   ├── schema.sql           # D1 schema (all 5 tables)
│   │   └── client.ts            # D1 client wrapper
│   ├── stages/
│   │   ├── ingest.ts            # Writes raw_sms
│   │   ├── parse.ts             # Reads raw_sms, writes parsed_transactions
│   │   ├── ledger.ts            # Reads parsed_transactions, writes ledger_entries
│   │   └── export.ts            # Reads ledger_entries, writes exports, calls targets
│   ├── parsers/                 # BANK RULES LIVE HERE (separate from engine)
│   │   ├── index.ts             # Parser registry
│   │   ├── base.ts              # Base parser interface
│   │   └── [bank-name].ts       # One file per bank (will add as we go)
│   ├── models/
│   │   ├── raw-sms.ts
│   │   ├── parsed-transaction.ts
│   │   ├── ledger-entry.ts
│   │   └── export.ts
│   ├── consumers/               # Export targets
│   │   ├── nas.ts               # NAS export (priority #1)
│   │   └── kubera.ts            # Kubera export (will integrate later)
│   └── utils/
│       ├── idempotency.ts       # Hash SMS for deduplication
│       └── processing-state.ts  # Cursor tracking helpers
├── test/
│   └── fixtures/
│       └── sms-samples.json     # Real SMS examples (I'll provide)
├── wrangler.toml
├── package.json
└── README.md
```

## Project Management Setup

### GitHub Setup Required
Before writing code, set up project management:

1. **Create GitHub Issues for Each Work Slice:**
   - Issue #1: D1 schema + basic Worker with POST /ingest
   - Issue #2: Add parsed_transactions table + single bank parser
   - Issue #3: Add Workflow orchestration calling parse stage
   - Issue #4: Add ledger_entries table + promotion logic
   - Issue #5: Add NAS export integration
   - Issue #6: Add idempotency (hash SMS, reject duplicates)
   - Issue #7: Add processing_state table + cursor tracking
   - Issue #8: Extract parser to separate file + registry
   - Issue #9: Add second bank parser
   - Issue #10: Add error handling + parse_errors table
   - Issue #11: Add GET /status endpoint
   - Issue #12: Document replay process

2. **Create GitHub Project Board:**
   - Columns: Backlog, In Progress, Testing, Done
   - Add all 12 issues to Backlog
   - Move issues through board as we work

3. **Create Milestones:**
   - Milestone 1: "Single Bank MVP" (Issues #1-5) - Due: 2 weeks
   - Milestone 2: "Production Ready" (Issues #6-9) - Due: 4 weeks  
   - Milestone 3: "Hardened" (Issues #10-12) - Due: 6 weeks

## Work Approach: Vertical Slices

Each slice must be:
- Independently testable (can verify with curl or SQL query)
- End-to-end (touches ingest → export path)
- Deployable (can push to Cloudflare and see it work)

**Always complete one slice before starting the next.**

## What You'll Provide Later (Don't Block on These Now)

### When We Get to Slice #2 (Parsing):
- Real SMS examples from primary Saudi bank (you have these ready)
- The bank's SMS sender ID/pattern
- Fields to extract (amount, date, merchant, account digits)

### When We Get to Slice #5 (Export):
- NAS database details (Postgres/MySQL/etc)
- Connection method (how Worker reaches NAS)
- Table schema for NAS database

### When We Get to Kubera Integration (Later):
- Existing Kubera client code
- Account mapping file structure
- Kubera API authentication details

## Current Task: Issue #2 - SMS Parsing

**Objective:** Add parsed_transactions table and implement first bank parser

**What needs to be done:**
1. Add `parsed_transactions` table to schema
2. Create base parser interface (`src/parsers/base.ts`)
3. Implement first bank-specific parser (`src/parsers/[bank-name].ts`)
4. Create parse stage (`src/stages/parse.ts`)
5. Test parsing with real SMS from database

**Database has real SMS ready to parse:**
- Check current SMS: `wrangler d1 execute sms-banking-db --remote --command "SELECT * FROM raw_sms"`
- 4 SMS waiting (includes Arabic text)

**User will provide:**
- Real SMS examples from their primary Saudi bank
- Bank's SMS sender ID
- Which fields to extract (amount, merchant, date, etc.)

## Key Principles

**Separation of Concerns:**
- Engine logic (stages/, db/, utils/) = generic, reusable
- Bank rules (parsers/) = specific extraction patterns
- To add new bank: create new parser file, register it

**Idempotency:**
- Event ID = hash(body + sender + received_at) on raw_sms
- UNIQUE constraints prevent duplicate processing
- Cursors allow safe replays

**Replay Safety:**
- Can reset cursor and reprocess from any stage
- Projections are rebuildable from source
- Raw SMS never mutates

## Important Implementation Details

### iOS Shortcuts Automation
- **Trigger**: Message Contains ` ` (single space = catch-all)
- **Shortcut Name**: "SMS Forwarding to Cloudflare"
- **Actions**:
  1. Format Date (ISO 8601 with time enabled)
  2. HTTP POST to /ingest
  3. JSON body: {body, sender, received_at}
- **Setup Guide**: `docs/SHORTCUT_SETUP.md`

### Logging & Observability
- Cloudflare logs enabled (`wrangler tail --format pretty`)
- Invocation logs enabled
- Traces enabled
- All configured in `wrangler.toml`

### Database Queries
- View all SMS: `wrangler d1 execute sms-banking-db --remote --command "SELECT * FROM raw_sms"`
- Count: `wrangler d1 execute sms-banking-db --remote --command "SELECT COUNT(*) FROM raw_sms"`
- Full query reference: `docs/DATABASE_QUERIES.md`

### Production Deployment
- Deploy: `npm run deploy`
- Database init: `npm run db:init` (with `--remote` flag for production)
- Worker URL: https://bank-sms-ledger.abdullah-915.workers.dev

## Questions to Ask Me

When you need:
- SMS format examples → "Show me a real SMS from [bank]"
- Export target details → "What's the NAS database schema?"
- Architecture clarification → "Should I implement X or Y?"
- Testing verification → "Did this work correctly?"

Don't assume - ask when you need context only I can provide.

<claude-mem-context>
# Recent Activity

<!-- This section is auto-generated by claude-mem. Edit content outside the tags. -->

### Jan 28, 2026

| ID | Time | T | Title | Read |
|----|------|---|-------|------|
| #157 | 12:22 AM | 🔵 | SMS Banking System Architecture and Build Plan | ~472 |
</claude-mem-context>