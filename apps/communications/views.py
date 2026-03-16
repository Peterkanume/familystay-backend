from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from .models import Conversation, Message, Notification
from .serializers import (
    ConversationSerializer, ConversationDetailSerializer,
    MessageSerializer, MessageCreateSerializer,
    NotificationSerializer
)
from apps.accounts.permissions import CanAccessConversation


class ConversationListView(generics.ListAPIView):
    """List user's conversations"""
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related('participants')


class ConversationDetailView(generics.RetrieveAPIView):
    """Get conversation details with messages"""
    serializer_class = ConversationDetailSerializer
    permission_classes = [CanAccessConversation]
    
    def get_queryset(self):
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related('participants', 'messages')


class CreateConversationView(generics.CreateAPIView):
    """Create a new conversation"""
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        participant_ids = request.data.get('participants', [])
        property_id = request.data.get('property_id')
        
        # Add current user to participants
        participant_ids.append(request.user.id)
        
        # Check if conversation already exists
        existing = Conversation.objects.filter(
            participants__in=participant_ids
        ).annotate(
            num_participants=models.Count('participants')
        ).filter(
            num_participants=len(participant_ids),
            property_id=property_id
        ).first()
        
        if existing:
            return Response(
                ConversationSerializer(existing, context={'request': request}).data
            )
        
        conversation = Conversation.objects.create(property_id=property_id)
        conversation.participants.set(participant_ids)
        
        return Response(
            ConversationSerializer(conversation, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class SendMessageView(APIView):
    """Send a message in a conversation"""
    permission_classes = [CanAccessConversation]
    
    def post(self, request, conversation_id):
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user
        )
        
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=serializer.validated_data['content'],
            attachments=serializer.validated_data.get('attachments', [])
        )
        
        # Update conversation timestamp
        conversation.save()
        
        # Create notifications for other participants
        for participant in conversation.participants.all():
            if participant != request.user:
                Notification.objects.create(
                    user=participant,
                    type='MESSAGE_RECEIVED',
                    title='New Message',
                    message=f"{request.user.get_full_name() or request.user.username} sent you a message",
                    data={
                        'conversation_id': conversation.id,
                        'message_id': message.id
                    }
                )
        
        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED
        )


class MarkAsReadView(APIView):
    """Mark messages as read"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, message_id):
        message = get_object_or_404(Message, id=message_id)
        
        # Check if user is participant in conversation
        if request.user not in message.conversation.participants.all():
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if message.sender != request.user:
            message.is_read = True
            message.read_at = timezone.now()
            message.save(update_fields=['is_read', 'read_at'])
        
        return Response({'message': 'Marked as read'})


class MyNotificationsView(generics.ListAPIView):
    """List user's notifications"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        
        # Filter by read status
        unread_only = self.request.query_params.get('unread')
        if unread_only and unread_only.lower() == 'true':
            queryset = queryset.filter(is_read=False)
        
        return queryset


class MarkNotificationReadView(APIView):
    """Mark a notification as read"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, notification_id):
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            user=request.user
        )
        
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at'])
        
        return Response({'message': 'Notification marked as read'})


class MarkAllNotificationsReadView(APIView):
    """Mark all notifications as read"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({'message': 'All notifications marked as read'})


# Import models
from django.db import models
