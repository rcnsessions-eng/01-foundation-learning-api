# PRD 01 Scope

- Implement only Secure Learning API Foundation from the attached PRD 01.
- Keep FastAPI routes, services and repositories separate; use synthetic fixtures only.
- Demo credentials are local teaching fixtures, not real authentication or cryptography.
- Ignore identity/tenant/role headers; use the resolved demo principal and scoped repository methods.
- Unknown and inaccessible resources share a safe error shape. Never include tokens, records or input payloads in logs/errors.
- Run `bash scripts/check.sh` and the Compose HTTP smoke before claiming acceptance.
- Do not add OPA, MCP, a real identity provider, database, model provider or Istio here. Those belong in their own numbered PRD code folders.
- Do not mark later milestones complete from prepared configuration or unexecuted tests.