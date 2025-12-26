from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView, TemplateView

from construction.models import ConstructionProject

from .models import Conversation, Message


class ConversationAccessMixin(LoginRequiredMixin):
    conversation_param = "pk"

    def get_conversation(self) -> Conversation:
        pk = self.kwargs.get(self.conversation_param)
        conversation = get_object_or_404(
            Conversation.objects.select_related("project", "customer"), pk=pk
        )
        user = self.request.user
        if user.is_staff or conversation.customer_id == user.id:
            return conversation
        raise Http404


class ConversationListView(UserPassesTestMixin, ListView):
    model = Conversation
    template_name = "chat/conversation_list.html"
    context_object_name = "conversations"

    def test_func(self) -> bool:
        return self.request.user.is_staff

    def get_queryset(self):
        return Conversation.objects.select_related(
            "project",
            "customer",
            "project__quote",
            "project__quote__design",
        ).prefetch_related("messages").order_by("-messages__timestamp", "-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_conversation_id"] = self.request.GET.get("conversation")
        return context


class ProjectConversationRedirectView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, project_pk: int) -> HttpResponse:
        project = get_object_or_404(
            ConstructionProject.objects.select_related("owner"), pk=project_pk
        )
        user = request.user
        if not (user.is_staff or project.owner_id == user.id):
            raise Http404
        conversation, _ = Conversation.objects.get_or_create(
            project=project,
            defaults={"customer": project.owner},
        )
        return redirect("chat:room", pk=conversation.pk)


class ChatRoomView(ConversationAccessMixin, TemplateView):
    template_name = "chat/chat_room.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = self.get_conversation()
        conversation.messages.filter(is_read=False).exclude(sender=self.request.user).update(is_read=True)
        context["conversation"] = conversation
        context["project"] = conversation.project
        context["messages"] = conversation.messages.select_related("sender")
        return context


class MessageListView(ConversationAccessMixin, TemplateView):
    template_name = "chat/partials/message_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = self.get_conversation()
        conversation.messages.filter(is_read=False).exclude(sender=self.request.user).update(is_read=True)
        messages_qs = conversation.messages.select_related("sender")
        context["conversation"] = conversation
        context["messages"] = messages_qs
        return context


class MessageCreateView(ConversationAccessMixin, View):
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        conversation = self.get_conversation()
        content = request.POST.get("content", "").strip()
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content,
            )
        messages_qs = conversation.messages.select_related("sender")
        context = {
            "conversation": conversation,
            "messages": messages_qs,
        }
        if request.headers.get("HX-Request"):
            return render(request, "chat/partials/message_list.html", context)
        return redirect("chat:room", pk=conversation.pk)