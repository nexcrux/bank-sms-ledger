/**
 * Raw SMS model - represents immutable SMS as received
 */
export interface RawSMS {
  id: number;
  body: string;
  sender: string;
  received_at: string;
  event_id: string;
  created_at: string;
}

/**
 * Input for creating a new SMS record
 */
export interface IngestSMSInput {
  body: string;
  sender: string;
  received_at: string;
}
