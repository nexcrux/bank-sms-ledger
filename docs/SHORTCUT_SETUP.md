# iOS Shortcuts Setup - SMS Forwarding to Cloudflare

## Part 1: Create the Automation Trigger

1. Open **Shortcuts** app
2. Tap **Automation** tab (bottom)
3. Tap **+** (top right)
4. Select **Create Personal Automation**
5. Select **Message**
6. Tap **Message Contains**
7. Type a single space: ` `
8. Enable **Run Immediately** ✓
9. Tap **Next**

## Part 2: Create the Shortcut Action

### Configure Action to Run Shortcut

1. Search: `Run Shortcut`
2. Add **Run Shortcut**
3. Tap **Shortcut** dropdown
4. Select **+ New Shortcut**
5. Name it: `SMS Forwarding to Cloudflare`
6. Tap **Done**

## Part 3: Build the SMS Forwarding Shortcut

### Open the New Shortcut for Editing

1. Go to **Shortcuts** tab (bottom)
2. Find and tap **SMS Forwarding to Cloudflare**

### Action 1: Format Time

1. Search: `Format Date`
2. Add **Format Date**
3. Tap **Date Format** dropdown
4. Select **ISO 8601**
5. Enable **Include ISO 8601 Time** ✓

### Action 2: Get Contents of URL

1. Search: `Get Contents of URL`
2. Add **Get Contents of URL**
3. Tap **URL** field
4. Enter: `https://bank-sms-ledger.abdullah-915.workers.dev/ingest`
5. Tap **Show More**
6. Tap **Method** → Select **POST**

### Action 3: Add Headers

1. Under **Headers**, tap **Add new field**
2. Select **Add Header**
3. Key: `Content-Type`
4. Value: `application/json`

### Action 4: Configure Request Body

1. Tap **Request Body** dropdown
2. Select **JSON**

### Action 5: Build JSON Structure

**Add Field #1: body**
1. Tap **Add new field**
2. Key: `body`
3. Type: **Text**
4. Value: Tap field → Select **Shortcut Input**

**Add Field #2: sender**
1. Tap **Add new field**
2. Key: `sender`
3. Type: **Text**
4. Value: Tap field → Select **Shortcut Input**
5. Tap the **Shortcut Input** pill
6. Select **Get Property** → Choose **Sender**

**Add Field #3: received_at**
1. Tap **Add new field**
2. Key: `received_at`
3. Type: **Text**
4. Value: Tap field → Select **Formatted Date**

### Final Steps

1. Tap **Done** (top right)
2. Go back to **Automation** tab
3. Verify your automation shows:
   - **When**: Message Contains " "
   - **Do**: Run Shortcut "SMS Forwarding to Cloudflare"
   - **Run Immediately**: ✓ Enabled

## Testing

1. Send yourself a test SMS from another phone
2. Automation should run automatically
3. Check database:
   ```bash
   wrangler d1 execute sms-banking-db --remote \
     --command "SELECT * FROM raw_sms ORDER BY id DESC LIMIT 1"
   ```

## Expected JSON Output

```json
{
  "body": "The SMS message text",
  "sender": "+966501234567",
  "received_at": "2026-01-30T12:53:41Z"
}
```

## Troubleshooting

### Automation doesn't trigger
- Check "Run Immediately" is enabled
- Verify message contains criterion is a single space

### HTTP request fails
- Verify URL is exactly: `https://bank-sms-ledger.abdullah-915.workers.dev/ingest`
- Check Headers: Content-Type = application/json
- Verify Method is POST

### Date format error
- Ensure "Format Date" action uses ISO 8601
- Enable "Include ISO 8601 Time"
- Use "Formatted Date" variable in received_at field

### Sender not captured
- Ensure sender field uses: Shortcut Input → Get Property → Sender
- Not just "Shortcut Input" alone
