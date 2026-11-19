# Operations

The API is intentionally stateless aside from in-process conversation history. For production, run behind authentication/TLS and move history/results to a protected store. Keep the reader account separate from migration/seeding credentials. The `DATABASE_ADMIN_URL` is used only by the seed tool and must never be passed to the API container in a production compose override.

Prometheus metrics include `analyst_requests_total` labelled by outcome and `analyst_response_seconds`. Configure alerts for error/rejection spikes and latency changes. Evaluation results are environment-specific because local model and hardware affect output and latency.
