set shell := ["bash", "-uc"]
set dotenv-load := true
set dotenv-filename := ".env"

python := ".venv/bin/python"

show-database:
    @if [ -n "${DATABASE_URL:-}" ]; then echo "DATABASE_URL is set"; else echo "DATABASE_URL is not set; Django will use local SQLite"; fi

source-env:
    @if [ ! -f .env ]; then echo ".env file not found"; exit 1; fi
    @if [ -n "${DATABASE_URL:-}" ]; then echo ".env loaded: DATABASE_URL is set"; else echo ".env loaded but DATABASE_URL is missing"; exit 1; fi

set-database-url:
    @if [ -z "${DATABASE_URL:-}" ]; then \
      echo "DATABASE_URL is not set. Export it in your shell or put it in .env."; \
      exit 1; \
    fi
    @echo "DATABASE_URL is set"

dev:
    {{python}} manage.py migrate
    {{python}} manage.py runserver 127.0.0.1:8000

migrate-supabase: set-database-url
    {{python}} -c 'import os, sys; os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mcq_app.settings"); import django; django.setup(); from django.conf import settings; db=settings.DATABASES["default"]; print(db["ENGINE"]); print(db.get("HOST","")); sys.exit("Refusing to migrate: configured database is not PostgreSQL.") if db["ENGINE"] != "django.db.backends.postgresql" else None'
    {{python}} manage.py migrate

sync-supabase: set-database-url
    {{python}} manage.py migrate
    {{python}} manage.py sync_topics_to_supabase quiz_topics

sync-supabase-dry-run:
    {{python}} manage.py migrate
    {{python}} manage.py sync_topics_to_supabase quiz_topics --dry-run

sync-supabase-deactivate-missing:
    {{python}} manage.py migrate
    {{python}} manage.py sync_topics_to_supabase quiz_topics --deactivate-missing

build-electron-application:
    {{python}} scripts/build_electron_for_current_os.py
