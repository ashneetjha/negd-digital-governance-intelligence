# n8n Recommendation (Architecture-Only)

This project should remain fully functional without n8n.  
n8n can be added as an orchestration layer for operational automation.

## Recommended Workflows

1. Monthly Ingestion Trigger
- Trigger: Scheduled cron (monthly) or incoming webhook.
- Steps:
  - Fetch report metadata from source (email/drive/form system).
  - Call backend `/api/ingest` per report.
  - Persist workflow run status in n8n execution logs.
- Outcome: Automated intake of monthly state submissions.

2. Failed Ingestion Alert
- Trigger: Poll `/api/reports` for `processed_status=failed`.
- Steps:
  - Aggregate failed report IDs and states.
  - Send alert to operations email/Slack/Teams.
  - Include error message and retry link.
- Outcome: Faster recovery from parsing/embedding failures.

3. Weekly Health Summary
- Trigger: Weekly cron.
- Steps:
  - Call `/health` and `/api/system/status`.
  - Create dependency health summary (Supabase, Embeddings, Groq, strict mode).
  - Send summary to stakeholders.
- Outcome: Proactive reliability monitoring.

## Integration Boundaries

- Keep n8n outside core request path.
- Never block frontend/backend user flows on n8n availability.
- Use secure credentials in n8n vault; avoid hardcoding keys in workflows.
- Prefer idempotent webhook payloads to avoid duplicate ingestion.

## Rollout Order

1. Add weekly health summary workflow.
2. Add failed-ingestion alert workflow.
3. Add monthly ingestion trigger workflow.
