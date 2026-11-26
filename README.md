# Takhti Backend

API and background workers for Takhti, the school operating system for Pakistani schools.

## Stack

Python 3.14 · Django 6.1 · Django REST Framework · PostgreSQL · Redis · Celery · uv

## Getting started

```bash
cp .env.example .env
docker compose up -d db redis
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

API docs are served at `http://localhost:8000/api/docs/`.

## Tenant isolation

Every request runs inside one organisation, chosen by the `X-Organisation` header (or the user's only organisation) and optionally narrowed by `X-Campus`.

- `Model.objects` on tenant-owned models is scoped to the current organisation and returns nothing outside one. `Model.unscoped` is for deliberate cross-tenant work such as the admin and the signed-in user's own memberships.
- PostgreSQL row-level security is the backstop. Policies read `app.organisation_id`, `app.user_id` and `app.is_system`, which the tenant middleware sets per request.
- Superusers and roles with `BYPASSRLS` ignore these policies. In production the app must connect as a role without either; the table owner is fine because the tables use `FORCE ROW LEVEL SECURITY`.

## Quality

```bash
uv run ruff format .
uv run ruff check .
uv run mypy .
uv run pytest
```
