# Secure Learning API Foundation

This code folder implements **only the foundation workshop**. It provides a FastAPI API with two synthetic tenants, three learners, two courses, approved/draft content and progress records. There is no OPA, MCP, persistent database, model, real identity provider or Istio here.

## Docker Compose

From this `code/` directory, with Docker and Docker Compose installed:

```bash
docker compose up -d --build --wait api
curl http://127.0.0.1:8220/health
curl -H 'Authorization: Bearer demo-learner-red' http://127.0.0.1:8220/v1/content
curl -H 'Authorization: Bearer demo-learner-red' http://127.0.0.1:8220/v1/learners/learner-red-1/progress
bash scripts/check.sh
python3 scripts/smoke.py
```

Local OpenAPI UI: <http://127.0.0.1:8220/docs>. The API runs as UID 10001 with a read-only filesystem, bounded temporary storage, dropped capabilities and no privilege escalation. Published ports bind loopback only. `LEARNING_PORT` overrides the host port; use `LEARNING_BASE_URL` for the smoke script when changing it. `LEARNING_SUBNET` overrides the dedicated Compose subnet if it conflicts with an existing network.

No `.env` is required for the public synthetic demo. `.env.example` contains a placeholder credential mapping. To customize it, create a local ignored `.env` and replace the placeholder; its credential must map to one of the seeded learner IDs. Use `LEARNING_SMOKE_CREDENTIAL` when running smoke with a replacement credential for `learner-red-1`. Do not expose this demo to an untrusted network: the documented defaults are public and are **not production authentication**. Demo identity is accepted only with `LEARNING_ENVIRONMENT=local`.

## Local Python

Use Python 3.12; later Python versions are not yet verified.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -c requirements.lock '.[dev]'
ruff check app tests
ruff format --check app tests
mypy app
python -m pytest
uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8220 --no-access-log
```

The default test suite requires no external services. Docker builds use exact direct pins and the resolved dependency constraints; dependency artifact hashes and base-image digest verification belong to the supply-chain workshop, not this milestone.

## Layers and Behavior

- `app/api/`: HTTP contracts and dependency injection; no record-access business logic.
- `app/services/`: owner checks, safe errors and minimal response projections.
- `app/repositories/`: typed interface and tenant-scoped in-memory fixture lookup.
- `app/auth/`: local-only bearer credential -> trusted synthetic principal mapping. No invented signed token format.
- `app/config.py`: startup validation; credential values excluded from configuration representations.
- `tests/`: positive, negative, configuration and logging tests.

`GET /health` returns status/version without authentication. Content and progress require a valid demo bearer credential. Red learner 1 uses `demo-learner-red`, red learner 2 uses `demo-learner-red-second`, and blue learner 1 uses `demo-learner-blue`. These are public teaching values. Unauthenticated requests return 401; malformed requests return 422; unknown, foreign and non-owned progress return the same 404 resource error. No denied response contains progress fields.

Request IDs are propagated only when they match a bounded printable identifier and are not configured credentials; otherwise a UUID is generated. Caller-supplied IDs must contain no private values. Structured `http_request` events include canonical route, ID, method, status and duration, never bearer values, query strings or records. Uvicorn access logging is disabled. Unexpected repository failures return a generic 500 without exposing exception details.

## Cleanup and Limits

```bash
docker compose down
```

Cleanup touches only this Compose project; no persistent learner data or database volumes exist. State resets with each API instance. Application-layer fixture scoping is demonstrated, not production tenant isolation, cryptographic identity, mesh encryption or certification. Kubernetes, scans, SBOMs and signing are not implemented by this foundation workshop. Verification evidence is maintained in the parent `docs/` directory.