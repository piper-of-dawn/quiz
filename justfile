set shell := ["bash", "-uc"]
set dotenv-load := true
set dotenv-filename := ".env"

python := ".venv/bin/python"

show-database:
    @if [ -n "${DATABASE_URL:-}" ]; then echo "DATABASE_URL is set"; else echo "DATABASE_URL is not set; Django will use local SQLite"; fi

set-database-url:
    @touch .env
    @if grep -q '^DATABASE_URL=' .env; then \
      perl -0pi -e "s#^DATABASE_URL=.*$#DATABASE_URL=postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres#m" .env; \
    else \
      printf '%s\n' 'DATABASE_URL=postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres' >> .env; \
    fi
    @echo "DATABASE_URL written to .env"

dev:
    {{python}} manage.py migrate
    {{python}} manage.py runserver 127.0.0.1:8000

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
