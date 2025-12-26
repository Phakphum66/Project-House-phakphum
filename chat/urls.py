from django.urls import path

from .views import (
    ChatRoomView,
    ConversationListView,
    MessageCreateView,
    MessageListView,
    ProjectConversationRedirectView,
)

app_name = "chat"

urlpatterns = [
    path("inbox/", ConversationListView.as_view(), name="inbox"),
    path("project/<int:project_pk>/", ProjectConversationRedirectView.as_view(), name="project"),
    path("conversations/<int:pk>/", ChatRoomView.as_view(), name="room"),
    path("conversations/<int:pk>/messages/", MessageListView.as_view(), name="messages"),
    path("conversations/<int:pk>/send/", MessageCreateView.as_view(), name="send"),
]
