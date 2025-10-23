# Airflow ETL — PGCB Pipeline

Local Apache Airflow (2.10.5, LocalExecutor) that will download PGCB daily reports,
extract them, and load to the analytics/serving layer.

## Layout
```
airflow/
├── Dockerfile            # airflow + project data deps (no Chrome; DAG uses bs4)
├── docker-compose.yaml   # postgres + init + webserver + scheduler
├── requirements.txt      # extra python deps baked into the image
├── .env                  # secrets (gitignored) — UID, Fernet, Supabase creds
├── .env.example          # template
└── dags/
    └── pipeline_healthcheck.py   # smoke test (delete after Phase 5)
```
The repo root is mounted **read-write** at `/opt/project` inside the containers,
so DAGs can call `script/` and read/write `daily_report*` + `extracted_data`.

## Boot
```bash
cd airflow
docker compose build          # first time, ~few min
docker compose up airflow-init   # one-shot: db migrate + create admin user
docker compose up -d          # start webserver + scheduler
```
UI: http://localhost:8080  (admin / admin)

Trigger `pipeline_healthcheck` from the UI. All 3 tasks green = stack + mounts + deps OK.

## Stop / reset
```bash
docker compose down            # stop
docker compose down -v         # stop + wipe metadata DB
```

## Roadmap
- [x] Phase 1 — scaffold
- [ ] Phase 2 — boot + healthcheck green
- [ ] Phase 3 — package `script/` (fix imports)
- [ ] Phase 4 — load layer (`db.py` + Supabase) ← migrate Supabase first
- [ ] Phase 5 — `daily_etl` DAG (download → rename → extract → load)
- [ ] Phase 6 — retries, alerting, backfill guard, Airflow Connections for secrets
