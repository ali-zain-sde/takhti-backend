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

## Quality

```bash
uv run ruff format .
uv run ruff check .
uv run mypy .
uv run pytest
```
