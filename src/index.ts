import { ingestSMS } from './stages/ingest';
import { IngestSMSInput } from './models/raw-sms';

/**
 * Cloudflare Workers environment with D1 binding
 */
export interface Env {
  DB: D1Database;
}

/**
 * Main Worker request handler
 */
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // POST /ingest - Accept SMS and write to raw_sms table
    if (url.pathname === '/ingest' && request.method === 'POST') {
      try {
        // Parse request body
        const input: IngestSMSInput = await request.json();

        // Validate required fields
        if (!input.body || !input.sender || !input.received_at) {
          return new Response(
            JSON.stringify({
              error: 'Missing required fields: body, sender, received_at'
            }),
            {
              status: 400,
              headers: { 'Content-Type': 'application/json' }
            }
          );
        }

        // Validate ISO 8601 timestamp format
        if (isNaN(Date.parse(input.received_at))) {
          return new Response(
            JSON.stringify({
              error: 'received_at must be a valid ISO 8601 timestamp'
            }),
            {
              status: 400,
              headers: { 'Content-Type': 'application/json' }
            }
          );
        }

        // Ingest SMS
        const result = await ingestSMS(env.DB, input);

        if (result === null) {
          // Duplicate SMS - idempotent response
          return new Response(
            JSON.stringify({
              message: 'SMS already processed (duplicate)',
              duplicate: true
            }),
            {
              status: 200,
              headers: { 'Content-Type': 'application/json' }
            }
          );
        }

        // Success - return created record
        return new Response(
          JSON.stringify({
            message: 'SMS ingested successfully',
            data: result
          }),
          {
            status: 201,
            headers: { 'Content-Type': 'application/json' }
          }
        );
      } catch (error: any) {
        console.error('Error ingesting SMS:', error);
        return new Response(
          JSON.stringify({
            error: 'Internal server error',
            message: error.message
          }),
          {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
          }
        );
      }
    }

    // GET / - Health check
    if (url.pathname === '/' && request.method === 'GET') {
      return new Response(
        JSON.stringify({
          service: 'SMS Banking Ledger',
          version: '1.0.0',
          status: 'healthy'
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    }

    // 404 for unknown routes
    return new Response(
      JSON.stringify({ error: 'Not found' }),
      {
        status: 404,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  },
};
