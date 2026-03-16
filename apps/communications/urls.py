from django.urls import path
from .views import (
    ConversationListView, ConversationDetailView, CreateConversationView,
    SendMessageView, MarkAsReadView, MyNotificationsView,
    MarkNotificationReadView, MarkAllNotificationsReadView
)

urlpatterns = [
    # Conversation endpoints
    path('conversations/', ConversationListView.as_view(), name='conversation_list'),
    path('conversations/create/', CreateConversationView.as_view(), name='create_conversation'),
    path('conversations/<int:pk>/', ConversationDetailView.as_view(), name='conversation_detail'),
    path('conversations/<int:conversation_id>/send/', SendMessageView.as_view(), name='send_message'),
    
    # Message endpoints
    path('messages/<int:message_id>/read/', MarkAsReadView.as_view(), name='mark_message_read'),
    
    # Notification endpoints
    path('notifications/', MyNotificationsView.as_view(), name='notifications'),
    path('notifications/<int:notification_id>/read/', MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('notifications/read-all/', MarkAllNotificationsReadView.as_view(), name='mark_all_notifications_read'),
]
