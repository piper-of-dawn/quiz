# Minimal MCQ Quiz

Django quiz UI backed by Supabase Postgres. JSON files stay in the repo for easy editing, then sync into the database for runtime serving.

## Environment

Set `DATABASE_URL` to the Supabase Postgres transaction pooler URL for deployed/serverless use.

```bash
cp .env.example .env
$EDITOR .env
```

If `DATABASE_URL` is absent, Django falls back to local SQLite for development only.

The `justfile` loads `.env` automatically, so these work after editing `.env`:

```bash
just show-database
just sync-supabase
```

## JSON Authoring

Put editable topic files under `quiz_topics/`. Each file can be a list of questions or an object with `metadata` and `questions`.

```bash
just sync-supabase-dry-run
just sync-supabase
```

`just sync-supabase` validates all JSON, runs migrations, and upserts topics by slug.

## Electron

The Electron app is a thin native wrapper around the hosted web app.

```bash
APP_URL=https://your-deployed-quiz.example just build-electron-application
```

The recipe detects Linux, macOS, or Windows and builds the matching native artifact for the current OS.
