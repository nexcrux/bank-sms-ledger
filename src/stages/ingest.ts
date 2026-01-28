import { IngestSMSInput, RawSMS } from '../models/raw-sms';
import { generateEventId } from '../utils/idempotency';

/**
 * Ingests an SMS into the raw_sms table
 * Returns the created record or null if duplicate (idempotency check)
 */
export async function ingestSMS(
  db: D1Database,
  input: IngestSMSInput
): Promise<RawSMS | null> {
  // Generate event ID for idempotency
  const eventId = await generateEventId(
    input.body,
    input.sender,
    input.received_at
  );

  try {
    // Insert SMS with idempotency check (UNIQUE constraint on event_id)
    const result = await db
      .prepare(
        `INSERT INTO raw_sms (body, sender, received_at, event_id)
         VALUES (?, ?, ?, ?)
         RETURNING *`
      )
      .bind(input.body, input.sender, input.received_at, eventId)
      .first<RawSMS>();

    return result;
  } catch (error: any) {
    // Check if error is due to duplicate event_id (UNIQUE constraint violation)
    if (error.message?.includes('UNIQUE constraint failed')) {
      // This is expected for duplicate SMS - return null to indicate idempotent rejection
      return null;
    }

    // Re-throw other errors
    throw error;
  }
}
