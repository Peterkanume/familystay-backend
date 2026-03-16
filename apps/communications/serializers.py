from rest_framework import serializers
from .models import Conversation, Message, Notification
from apps.accounts.serializers import UserSerializer


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model"""
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'content', 'attachments', 
                  'is_read', 'read_at', 'created_at']
        read_only_fields = fields


class PropertySimpleSerializer(serializers.Serializer):
    """Simple property serializer for conversations"""
    id = serializers.IntegerField()
    title = serializers.CharField()
    featured_image = serializers.CharField(allow_null=True)
    address = serializers.CharField(allow_null=True)
    city = serializers.CharField(allow_null=True)


class LastMessageSerializer(serializers.Serializer):
    """Serializer for last message preview"""
    id = serializers.IntegerField()
    content = serializers.CharField()
    sender = serializers.CharField(source='sender.username')
    created_at = serializers.DateTimeField()


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for Conversation model"""
    participants = UserSerializer(many=True, read_only=True)
    property = PropertySimpleSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'property', 'booking', 'last_message', 
                  'unread_count', 'created_at', 'updated_at']
        read_only_fields = fields
    
    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            # Return a simple string for the last message content
            content = last_msg.content[:50] + '...' if len(last_msg.content) > 50 else last_msg.content
            return content
        return None
    
    def get_unread_count(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        if user and user.is_authenticated:
            return obj.messages.exclude(sender=user).filter(is_read=False).count()
        return 0


class ConversationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for conversation with messages"""
    participants = UserSerializer(many=True, read_only=True)
    property = PropertySimpleSerializer(read_only=True)
    messages = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'property', 'booking', 'messages', 
                  'created_at', 'updated_at']
        read_only_fields = fields
    
    def get_messages(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        messages = obj.messages.all().order_by('created_at')
        
        # Mark unread messages from other users as read
        if user and user.is_authenticated:
            unread_messages = messages.filter(is_read=False).exclude(sender=user)
            if unread_messages.exists():
                unread_messages.update(is_read=True)
        
        return MessageSerializer(messages, many=True).data


class MessageCreateSerializer(serializers.Serializer):
    """Serializer for creating a message"""
    content = serializers.CharField(min_length=1, max_length=5000)
    attachments = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        default=list
    )
    
    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Message cannot be empty")
        return value.strip()


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    
    class Meta:
        model = Notification
        fields = ['id', 'type', 'title', 'message', 'data', 'is_read', 
                  'read_at', 'created_at']
        read_only_fields = fields


class MarkMessageReadSerializer(serializers.Serializer):
    """Serializer for marking messages as read"""
    message_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )


class MarkAllReadSerializer(serializers.Serializer):
    """Serializer for marking all notifications as read"""
    pass