# Database Query Guide

Quick reference for querying your SMS banking database.

## Basic Command Structure

```bash
wrangler d1 execute sms-banking-db --remote --command "YOUR SQL QUERY HERE"
```

**Flags:**
- `--remote` = Query production database (in Cloudflare)
- Without `--remote` = Query local development database

---

## Common Queries

### View All SMS

```bash
wrangler d1 execute sms-banking-db --remote \
  --command "SELECT * FROM raw_sms ORDER BY id DESC"
```

### View Last 5 SMS

```bash
wrangler d1 execute sms-banking-db --remote \
  --command "SELECT * FROM raw_sms ORDER BY id DESC LIMIT 5"
```

### Count Total SMS

```bash
wrangler d1 execute sms-banking-db --remote \
  --command "SELECT COUNT(*) as total FROM raw_sms"
```

### View SMS by Sender

```bash
wrangler d1 execute sms-banking-db --remote \
  --command "SELECT * FROM raw_sms WHERE sender = 'AlRajhiBank' ORDER BY id DESC"
```

### Search SMS Body (Contains keyword)

```bash
wrangler d1 execute sms-banking-db --remote \
  --command "SELECT * FROM raw_sms WHERE body LIKE '%SAR%' ORDER BY id DESC"
```

### View SMS from Today

```bash
wrangler d1 execute sms-banking-db --remote \
  --command "SELECT * FROM raw_sms WHERE DATE(created_at) = DATE('now') ORDER BY id DESC"
```

### View Last 3 SMS (Compact View)

```bash
wrangler d1 execute sms-banking-db --remote \
  --command "SELECT id, sender, substr(body, 1, 50) || '...' as preview, created_at FROM raw_sms ORDER BY id DESC LIMIT 3"
```

### Get Latest SMS ID and Time

```bash
wrangler d1 execute sms-banking-db --remote \
  --command "SELECT MAX(id) as latest_id, MAX(created_at) as latest_time FROM raw_sms"
```

### List All Unique Senders

```bash
wrangler d1 execute sms-banking-db --remote \
  --command "SELECT DISTINCT sender, COUNT(*) as count FROM raw_sms GROUP BY sender ORDER BY count DESC"
```

### View Processing State (Cursors)

```bash
wrangler d1 execute sms-banking-db --remote \
  --command "SELECT * FROM processing_state"
```

### Delete Specific SMS (Use with caution!)

```bash
wrangler d1 execute sms-banking-db --remote \
  --command "DELETE FROM raw_sms WHERE id = 1"
```

### Clear All SMS (Use with caution!)

```bash
wrangler d1 execute sms-banking-db --remote \
  --command "DELETE FROM raw_sms"
```

---

## Alternative: Cloudflare Dashboard

You can also query the database via web browser:

1. Go to: https://dash.cloudflare.com
2. Navigate to: Workers & Pages → D1
3. Click on: `sms-banking-db`
4. Go to: "Console" tab
5. Type SQL query and click "Execute"

**Example queries to try:**
```sql
SELECT * FROM raw_sms ORDER BY id DESC LIMIT 10;

SELECT COUNT(*) FROM raw_sms;

SELECT sender, COUNT(*) as total
FROM raw_sms
GROUP BY sender;
```

---

## Useful Aliases (Optional)

Add these to your `~/.zshrc` or `~/.bashrc`:

```bash
# SMS Database shortcuts
alias sms-count="wrangler d1 execute sms-banking-db --remote --command 'SELECT COUNT(*) as total FROM raw_sms'"

alias sms-last="wrangler d1 execute sms-banking-db --remote --command 'SELECT * FROM raw_sms ORDER BY id DESC LIMIT 1'"

alias sms-list="wrangler d1 execute sms-banking-db --remote --command 'SELECT id, sender, substr(body, 1, 60) as preview FROM raw_sms ORDER BY id DESC LIMIT 5'"

alias sms-watch="watch -n 5 'wrangler d1 execute sms-banking-db --remote --command \"SELECT COUNT(*) as total FROM raw_sms\"'"
```

Then reload:
```bash
source ~/.zshrc
```

Now you can just type:
```bash
sms-count    # Get total count
sms-last     # Show latest SMS
sms-list     # Show last 5
```

---

## Monitoring Script

For real-time monitoring, use this script:

```bash
#!/bin/bash
# Save as: watch_sms.sh

LAST_COUNT=$(wrangler d1 execute sms-banking-db --remote \
  --command "SELECT COUNT(*) FROM raw_sms" 2>/dev/null | \
  grep -o '"COUNT(*)": [0-9]*' | cut -d' ' -f2)

echo "📱 Watching for new SMS... (Current: $LAST_COUNT)"
echo "Press Ctrl+C to stop"

while true; do
  NEW_COUNT=$(wrangler d1 execute sms-banking-db --remote \
    --command "SELECT COUNT(*) FROM raw_sms" 2>/dev/null | \
    grep -o '"COUNT(*)": [0-9]*' | cut -d' ' -f2)

  if [ "$NEW_COUNT" -gt "$LAST_COUNT" ]; then
    echo "🎉 NEW SMS! Total: $NEW_COUNT (was $LAST_COUNT)"
    wrangler d1 execute sms-banking-db --remote \
      --command "SELECT * FROM raw_sms ORDER BY id DESC LIMIT 1"
    LAST_COUNT=$NEW_COUNT
  fi

  sleep 5
done
```

---

## Tips

- Use `LIMIT` to avoid overwhelming output with large datasets
- Use `DESC` to see newest records first
- Use `LIKE '%keyword%'` for text search (case-insensitive)
- Remember to use `--remote` for production data
- SQL queries are case-insensitive: `SELECT` = `select`

---

## Database Schema Reference

### raw_sms Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-incrementing primary key |
| body | TEXT | Full SMS message text |
| sender | TEXT | Phone number or sender ID |
| received_at | TEXT | ISO 8601 timestamp |
| event_id | TEXT | SHA-256 hash for idempotency (UNIQUE) |
| created_at | TEXT | When record was inserted |

### processing_state Table

| Column | Type | Description |
|--------|------|-------------|
| stage | TEXT | Stage name (parse/ledger/export) |
| last_processed_id | INTEGER | Last processed SMS ID |
| last_processed_at | TEXT | Last processing timestamp |

---

## Need Help?

Check the main README.md for more examples and documentation.
