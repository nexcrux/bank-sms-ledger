# iOS Shortcuts Setup for Automatic SMS Forwarding

## Quick Setup Guide

### 1. Create New Automation

1. Open **Shortcuts** app
2. Go to **Automation** tab
3. Tap **+** → **Create Personal Automation**
4. Select **Message**

### 2. Configure Trigger

**Option A: Specific Bank Sender**
- Choose "Sender"
- Select contact or type bank name: `AlRajhiBank`, `STC-Bank`, etc.
- This triggers only for that specific sender

**Option B: All Bank Messages** (if senders vary)
- Choose "Contains"
- Enter keyword like: `SAR`, `transaction`, `purchase`
- This triggers for any message containing that word

**Important:** Enable "Run Immediately" so it runs without confirmation

### 3. Add Actions

Tap **Add Action** and build this sequence:

#### Action 1: Get Current Date
- Search for "Date"
- Add "Current Date"
- This captures the timestamp

#### Action 2: Format Date to ISO 8601
- Search for "Format Date"
- Add "Format Date"
- Set format to: **ISO 8601**
- Result will be like: `2024-01-28T14:30:00Z`

#### Action 3: Get Message Details
- Search for "Get Details of Messages"
- Add "Get Details of Messages"
- Input: "Message" (from trigger)
- Select: "Sender" and "Message" (body text)

#### Action 4: Get URLs from Input
- Add "Get URLs from Input"
- Input: Use the formatted date from Action 2
- (We'll use this to construct our API request)

#### Action 5: Get Contents of URL (HTTP POST)
- Search for "Get Contents of URL"
- Add "Get Contents of URL"
- Configure:

```
URL: https://bank-sms-ledger.abdullah-915.workers.dev/ingest

Method: POST

Headers:
  Content-Type: application/json

Request Body (JSON):
{
  "body": "[Message from Get Details]",
  "sender": "[Sender from Get Details]",
  "received_at": "[Formatted Date]"
}
```

### 4. Detailed Action Configuration

Here's the exact configuration for the HTTP request:

**Get Contents of URL Action:**

- **URL**: `https://bank-sms-ledger.abdullah-915.workers.dev/ingest`
- **Method**: `POST`
- **Headers**: Add header
  - Key: `Content-Type`
  - Value: `application/json`
- **Request Body**: Select "JSON" format

**JSON Body Template:**
```json
{
  "body": "Message",
  "sender": "Sender",
  "received_at": "Formatted Date"
}
```

Replace the quoted values with variables from previous actions:
- Tap in the text field
- Select "Message" variable
- Select "Sender" variable
- Select "Formatted Date" variable

### 5. Test the Automation

**Method 1: Ask someone to send you a test SMS**
- Use the exact sender name you configured
- Include keywords like "SAR 50.00 transaction"

**Method 2: Use a second phone or online SMS service**
- Send yourself a test message

**Method 3: Wait for real bank SMS**
- Next time your bank sends an SMS, it will auto-forward

### 6. Verify It Worked

Check if SMS was received:
```bash
wrangler d1 execute sms-banking-db --remote --command "SELECT * FROM raw_sms ORDER BY id DESC LIMIT 5"
```

Or visit Cloudflare dashboard → D1 → sms-banking-db → Query

## Troubleshooting

### Automation doesn't trigger
- Check if "Run Immediately" is enabled
- Verify sender name matches exactly
- Check iPhone Settings → Shortcuts → Allow Running Scripts

### HTTP request fails
- Verify URL is correct
- Check internet connection
- Ensure JSON format is valid
- Check Shortcuts app logs (tap automation → View logs)

### Shows "Shortcuts wants to access..."
- This is normal first time
- Tap "Allow" to grant permissions

## Alternative: Trigger on Any Bank Keyword

If your bank uses multiple sender IDs, use this trigger instead:

**Trigger**: Message contains "SAR" (or "transaction", "purchase", etc.)

This catches messages from any sender that contains the keyword.

## Security Note

The endpoint is currently public. For production use, consider:
- Adding an API key header
- Using Cloudflare Access
- IP allowlisting (though iPhone IP changes)

For now, this is fine since:
- Data is not sensitive (you'll see these SMS anyway)
- Endpoint only accepts SMS data
- Idempotency prevents spam

## Next Steps

Once automation is working:
1. Let it collect SMS for a few days
2. Review data in database
3. Build parser (Issue #2) based on actual SMS format
4. Extend to other banks if needed

## Visual Guide

**Automation Overview:**
```
📱 Bank SMS arrives
    ↓
🤖 Shortcuts automation triggered
    ↓
📅 Capture timestamp (ISO 8601)
    ↓
🔍 Extract sender & body
    ↓
🌐 POST to Cloudflare /ingest
    ↓
☁️  Stored in D1 database
    ↓
✅ Done (< 1 second)
```

## Example SMS Formats to Expect

**Al Rajhi Bank:**
```
Dear Customer, SAR 150.00 has been debited from your account
ending 1234 at STARBUCKS on 28/01/2024. Available balance: SAR 5,000.00
```

**STC Pay:**
```
You paid SAR 50.00 to Amazon using card ending 5678.
Date: 28-01-2024 14:30:00
```

**SABB:**
```
Purchase Alert: Your card ending in 9012 was used for
SAR 200.00 at Carrefour on 28-Jan-2024
```

These will all be captured and we'll parse them in Issue #2!
