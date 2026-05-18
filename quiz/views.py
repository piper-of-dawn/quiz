import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import Topic
from .normalizers import normalize_questions, render_choice_html, render_rich_html


def healthz(request):
    return JsonResponse({"ok": True})


def topic_list(request):
    topics = Topic.objects.filter(is_active=True).only("title", "slug", "description", "updated_at")
    return render(request, "quiz/topic_list.html", {"topics": topics})


def topic_detail(request, slug):
    topic = get_object_or_404(Topic, slug=slug, is_active=True)
    questions = normalize_questions(topic.question_blob)
    enriched = []
    for index, question in enumerate(questions):
        explanation_html = render_rich_html(question.get("explanation") or "")
        choices = [
            (choice_index, choice, render_choice_html(choice))
            for choice_index, choice in enumerate(question.get("choices") or [])
        ]
        payload = {
            "text": question["text"],
            "choices": question["choices"],
            "answer": question["answer"],
            "explanation": question.get("explanation") or "",
            "explanation_html": str(explanation_html),
            "extras": question.get("extras") or {},
        }
        enriched.append(
            {
                "index": index,
                "text_html": render_rich_html(question["text"]),
                "choices": choices,
                "answer": question["answer"],
                "explanation": question.get("explanation") or "",
                "explanation_html": explanation_html,
                "extras": question.get("extras") or {},
                "json": json.dumps(payload, ensure_ascii=False),
            }
        )
    return render(
        request,
        "quiz/mcq.html",
        {
            "topic": topic,
            "questions": enriched,
            "total": len(enriched),
            "timer_seconds": len(enriched) * 60,
        },
    )
