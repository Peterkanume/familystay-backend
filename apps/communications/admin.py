from django.contrib import admin
from .models import Conversation, Message, Notification


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Conversation Admin"""
    list_display = ['id', 'property', 'booking', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['id', 'property__title', 'participants__username']
    filter_horizontal = ['participants']
    date_hierarchy = 'created_at'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Message Admin"""
    list_display = ['id', 'conversation', 'sender', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['conversation__id', 'sender__username', 'content']
    date_hierarchy = 'created_at'
    readonly_fields = ['conversation', 'sender', 'content', 'attachments', 'is_read', 'read_at', 'created_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Notification Admin"""
    list_display = ['id', 'user', 'type', 'title', 'is_read', 'created_at']
    list_filter = ['type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    date_hierarchy = 'created_at'
    list_editable = ['is_read']
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = 'Mark selected notifications as read'
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
    mark_as_unread.short_description = 'Mark selected notifications as unread'
