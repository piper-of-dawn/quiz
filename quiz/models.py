from django.db import models
from django.urls import reverse


class Topic(models.Model):
    title = models.CharField(max_length=220)
    slug = models.SlugField(unique=True, max_length=240)
    description = models.TextField(blank=True)
    question_blob = models.JSONField()
    source_path = models.CharField(max_length=500, blank=True)
    content_hash = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("topic_detail", kwargs={"slug": self.slug})
