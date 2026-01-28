-- SMS Banking System Database Schema

-- Table 1: raw_sms
-- Immutable source of truth - SMS messages as received, never modified
CREATE TABLE IF NOT EXISTS raw_sms (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  body TEXT NOT NULL,
  sender TEXT NOT NULL,
  received_at TEXT NOT NULL,  -- ISO 8601 timestamp
  event_id TEXT NOT NULL UNIQUE,  -- hash(body + sender + received_at) for idempotency
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Index for fast lookups by event_id
CREATE INDEX IF NOT EXISTS idx_raw_sms_event_id ON raw_sms(event_id);

-- Index for chronological queries
CREATE INDEX IF NOT EXISTS idx_raw_sms_created_at ON raw_sms(created_at);

-- Table 2: processing_state
-- Tracks cursor position for each processing stage
CREATE TABLE IF NOT EXISTS processing_state (
  stage TEXT PRIMARY KEY,  -- 'parse', 'ledger', 'export'
  last_processed_id INTEGER NOT NULL DEFAULT 0,
  last_processed_at TEXT  -- ISO 8601 timestamp of last processing run
);

-- Initialize processing stages
INSERT OR IGNORE INTO processing_state (stage, last_processed_id) VALUES ('parse', 0);
INSERT OR IGNORE INTO processing_state (stage, last_processed_id) VALUES ('ledger', 0);
INSERT OR IGNORE INTO processing_state (stage, last_processed_id) VALUES ('export', 0);
