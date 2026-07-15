# Status Monitor

A self-hosted uptime monitor: define services, it checks them on a schedule,
stores history, and shows a live dashboard with per-service uptime strips.

## Stack

- **API**: FastAPI + Jinja2 (serves both the JSON API and the dashboard HTML)
- **Database**: PostgreSQL
- **Cache**: Redis (latest-status cache, and the Celery broker/result backend)
- **Scheduler/worker**: Celery + Celery Beat (runs the actual health checks)

## Database schema

Three tables:

- **`services`** — what to monitor: name, URL, HTTP method, expected status
  code, check interval, active flag.
- **`checks`** — one row per health check ever run: status (up/down), status
  code, response time, error message, timestamp. This is the time-series
  table everything else is computed from.
- **`incidents`** — a continuous span of downtime for a service. Opened when
  a check first fails, resolved when a later check succeeds. Exists so you
  can answer "how many outages has this had" without scanning every row in
  `checks`.

`services` has a one-to-many relationship to both `checks` and `incidents`
(`service_id` foreign key, cascade delete — removing a service removes its
history).

## Running it locally

Requires Docker and Docker Compose.

```bash
git clone <your-repo-url> devops-status-monitor
cd devops-status-monitor
docker compose up --build
```

That starts five things: Postgres, Redis, the FastAPI app, a Celery worker,
and Celery beat. Tables are created automatically on API startup.

Open **http://localhost:8000** — you'll see an empty dashboard. Click
**+ Add service** and add something, e.g.:

- Name: `Example site`
- URL: `https://example.com`
- Method: `GET`
- Expected status: `200`
- Interval: `30`

Within a few seconds the beat scheduler fires, the worker checks it, and the
card updates with a status pill, response time, and the first block in its
uptime strip.

You can also add a service directly via the API:

```bash
curl -X POST http://localhost:8000/api/services \
  -H "Content-Type: application/json" \
  -d '{"name": "Example site", "url": "https://example.com", "method": "GET", "expected_status": 200, "check_interval_seconds": 30}'
```

Other useful endpoints:

- `GET /api/status` — everything the dashboard polls, in one call
- `GET /health` — liveness probe (used by Docker/Kubernetes health checks)
- `GET /metrics` — Prometheus-format metrics
- `GET /docs` — interactive OpenAPI docs (built into FastAPI)

To stop everything: `docker compose down`. Add `-v` to also wipe the
Postgres volume and start clean next time.

## Running without Docker (for development)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # point DATABASE_URL / REDIS_URL at local instances

uvicorn app.main:app --reload
# in separate terminals:
celery -A app.celery_app worker --loglevel=info
celery -A app.celery_app beat --loglevel=info
```

You'll need Postgres and Redis running locally (or point `.env` at any
reachable instance) for this to work.

## Notes / things a production version would add

- **Alembic migrations** instead of `Base.metadata.create_all()` — fine for
  a demo, but you want versioned, reversible schema changes in a real app.
- **Multiprocess Prometheus metrics** — the worker and API are separate
  processes, so `/metrics` recomputes gauges from the database on each
  scrape rather than incrementing counters in-process.
- **Retry/backoff** on the health-check HTTP calls for flaky networks.
