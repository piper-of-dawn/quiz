import hashlib
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from quiz.models import Topic
from quiz.normalizers import QuizBlobError, normalize_questions


class Command(BaseCommand):
    help = "Validate local JSON topic files and upsert them into the configured database."

    def add_arguments(self, parser):
        parser.add_argument("root", nargs="?", default="quiz_topics")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--deactivate-missing", action="store_true")

    def handle(self, *args, **options):
        root = Path(options["root"]).resolve()
        if not root.exists():
            raise CommandError(f"Topic JSON root does not exist: {root}")
        files = sorted(root.rglob("*.json"))
        if not files:
            self.stdout.write(self.style.WARNING(f"No JSON files found under {root}"))
            return

        seen_slugs = set()
        created = updated = skipped = 0
        for path in files:
            rel = path.relative_to(root).as_posix()
            raw_text = path.read_text(encoding="utf-8")
            try:
                blob = json.loads(raw_text)
                questions = normalize_questions(blob)
            except (json.JSONDecodeError, QuizBlobError) as exc:
                raise CommandError(f"{rel}: {exc}") from exc

            metadata = blob.get("metadata", {}) if isinstance(blob, dict) else {}
            title = str(metadata.get("title") or path.stem).strip()
            slug = str(metadata.get("slug") or slugify(path.with_suffix("").as_posix().replace("/", "-"))).strip()
            description = str(metadata.get("description") or "").strip()
            content_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
            seen_slugs.add(slug)

            existing = Topic.objects.filter(slug=slug).first()
            if existing and existing.content_hash == content_hash and existing.source_path == rel:
                skipped += 1
                self.stdout.write(f"skip   {slug} ({len(questions)} questions)")
                continue

            action = "update" if existing else "create"
            if options["dry_run"]:
                self.stdout.write(f"{action:<6} {slug} ({len(questions)} questions) [dry-run]")
                if existing:
                    updated += 1
                else:
                    created += 1
                continue

            Topic.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "description": description,
                    "question_blob": blob,
                    "source_path": rel,
                    "content_hash": content_hash,
                    "is_active": True,
                },
            )
            if existing:
                updated += 1
            else:
                created += 1
            self.stdout.write(self.style.SUCCESS(f"{action:<6} {slug} ({len(questions)} questions)"))

        deactivated = 0
        if options["deactivate_missing"] and not options["dry_run"]:
            deactivated = Topic.objects.exclude(slug__in=seen_slugs).update(is_active=False)
        elif options["deactivate_missing"] and options["dry_run"]:
            deactivated = Topic.objects.exclude(slug__in=seen_slugs).count()
            self.stdout.write(f"would deactivate {deactivated} missing topics [dry-run]")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {created} created, {updated} updated, {skipped} skipped, {deactivated} deactivated."
            )
        )
