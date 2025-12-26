from django.contrib import admin

from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("project", "customer", "created_at")
    search_fields = ("project__id", "project__quote__design__title", "customer__username")
    autocomplete_fields = ("customer", "project")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "sender", "timestamp", "is_read")
    list_filter = ("is_read", "timestamp")
    search_fields = ("conversation__project__quote__design__title", "sender__username", "content")
    autocomplete_fields = ("conversation", "sender")
