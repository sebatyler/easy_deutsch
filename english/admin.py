from django.contrib import admin

from .models import Vocabulary


@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = ("id", "word", "note", "conversation")
    list_filter = ("created", "modified")
    search_fields = ("=id", "word", "note", "conversation")
    readonly_fields = ("created", "modified")
