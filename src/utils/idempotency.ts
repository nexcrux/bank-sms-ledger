/**
 * Generates a deterministic event ID from SMS content
 * Used for idempotency - same SMS inputs always produce same hash
 */
export async function generateEventId(
  body: string,
  sender: string,
  receivedAt: string
): Promise<string> {
  const input = `${body}|${sender}|${receivedAt}`;
  const encoder = new TextEncoder();
  const data = encoder.encode(input);

  // SHA-256 hash
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

  // Return first 16 characters for brevity
  return hashHex.substring(0, 16);
}
