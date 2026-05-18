from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Topic
from .normalizers import normalize_questions


class NormalizerTests(TestCase):
    def test_normalizes_cfa_style_shape(self):
        questions = normalize_questions(
            [
                {
                    "stem": "Question?",
                    "options": {"A": "Alpha", "B": "Beta", "C": "Gamma"},
                    "correct_answer": "B",
                }
            ]
        )
        self.assertEqual(questions[0]["text"], "Question?")
        self.assertEqual(questions[0]["choices"], ["Alpha", "Beta", "Gamma"])
        self.assertEqual(questions[0]["answer"], 1)

    def test_normalizes_generic_shape(self):
        questions = normalize_questions({"questions": [{"text": "Q?", "choices": ["A", "B"], "answer": 0}]})
        self.assertEqual(questions[0]["answer"], 0)


class ViewTests(TestCase):
    def setUp(self):
        self.topic = Topic.objects.create(
            title="Sample Topic",
            slug="sample-topic",
            question_blob=[{"text": "Two plus two?", "choices": ["3", "4", "5"], "answer": 1}],
        )
        Topic.objects.create(
            title="Inactive Topic",
            slug="inactive-topic",
            is_active=False,
            question_blob=[{"text": "Hidden?", "choices": ["A"], "answer": 0}],
        )

    def test_topic_list_only_shows_active_topics(self):
        response = self.client.get(reverse("topic_list"))
        self.assertContains(response, "Sample Topic")
        self.assertNotContains(response, "Inactive Topic")

    def test_topic_detail_renders_questions_from_blob(self):
        response = self.client.get(reverse("topic_detail", kwargs={"slug": self.topic.slug}))
        self.assertContains(response, "Two plus two?")
        self.assertContains(response, "4")

    def test_healthz(self):
        response = self.client.get(reverse("healthz"))
        self.assertEqual(response.json(), {"ok": True})


class SyncCommandTests(TestCase):
    def test_sync_dry_run_validates_without_writing(self):
        call_command("sync_topics_to_supabase", "quiz_topics", "--dry-run", verbosity=0)
        self.assertEqual(Topic.objects.count(), 0)
