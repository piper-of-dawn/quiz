from django.contrib import admin
from django.urls import path

from quiz import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.topic_list, name="topic_list"),
    path("topics/<slug:slug>/", views.topic_detail, name="topic_detail"),
    path("healthz/", views.healthz, name="healthz"),
]
