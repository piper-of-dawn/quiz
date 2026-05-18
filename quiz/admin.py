from django.contrib import admin

from .models import Topic


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_active", "source_path", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "slug", "description", "source_path")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("content_hash", "created_at", "updated_at")
