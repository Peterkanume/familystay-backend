from django.db import models
from apps.accounts.models import User
from apps.bookings.models import Booking

class Conversation(models.Model):
    """Conversation between guest and host about a booking"""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='conversation', null=True, blank=True)
    participants = models.ManyToManyField(User, related_name='conversations')
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='conversations', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation {self.id} - {self.participants.count()} participants"

class Message(models.Model):
    """Individual messages in a conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    attachments = models.JSONField(default=list)  # List of file URLs
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender', 'is_read']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.username} at {self.created_at}"

class Notification(models.Model):
    """Push/in-app notifications for users"""
    
    class NotificationType(models.TextChoices):
        BOOKING_CONFIRMATION = 'BOOKING_CONFIRM', 'Booking Confirmation'
        PAYMENT_SUCCESS = 'PAYMENT_SUCCESS', 'Payment Successful'
        PAYMENT_FAILED = 'PAYMENT_FAILED', 'Payment Failed'
        BOOKING_CANCELLED = 'BOOKING_CANCELLED', 'Booking Cancelled'
        REVIEW_RECEIVED = 'REVIEW_RECEIVED', 'New Review'
        MESSAGE_RECEIVED = 'MESSAGE_RECEIVED', 'New Message'
        UPCOMING_STAY = 'UPCOMING_STAY', 'Upcoming Stay Reminder'
        PROPERTY_APPROVED = 'PROPERTY_APPROVED', 'Property Approved'
        PAYOUT_PROCESSED = 'PAYOUT_PROCESSED', 'Payout Processed'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=30, choices=NotificationType.choices)
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(default=dict)  # Additional data (booking ID, etc.)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.type} - {self.user.username}"