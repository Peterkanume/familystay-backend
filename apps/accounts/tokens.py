from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta


class CustomToken(models.Model):
    """
    Custom token model to track user activity and implement session timeout.
    This allows us to track when a user was last active and enforce inactivity timeout.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='custom_tokens'
    )
    key = models.CharField(max_length=255, unique=True)
    refresh_key = models.CharField(max_length=255, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    device_info = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = 'Custom Token'
        verbose_name_plural = 'Custom Tokens'
        ordering = ['-last_activity']

    def __str__(self):
        return f"Token for {self.user.username} - Last activity: {self.last_activity}"

    @property
    def is_expired(self):
        """Check if token has expired based on inactivity timeout"""
        # 30 minutes of inactivity timeout
        timeout = timedelta(minutes=30)
        return timezone.now() - self.last_activity > timeout

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])

    @classmethod
    def create_token(cls, user, refresh_token_key=None, device_info=None, ip_address=None):
        """Create a new custom token for a user"""
        # Generate unique keys
        from django.utils.crypto import get_random_string
        key = get_random_string(64)
        
        token = cls.objects.create(
            user=user,
            key=key,
            refresh_key=refresh_token_key,
            device_info=device_info,
            ip_address=ip_address
        )
        return token

    @classmethod
    def invalidate_user_tokens(cls, user):
        """Invalidate all tokens for a user (logout from all devices)"""
        cls.objects.filter(user=user, is_active=True).update(is_active=False)

    @classmethod
    def cleanup_expired_tokens(cls):
        """Remove expired tokens"""
        timeout = timedelta(minutes=30)
        expired_time = timezone.now() - timeout
        cls.objects.filter(last_activity__lt=expired_time, is_active=True).update(is_active=False)


def get_tokens_for_user(user):
    """
    Generate JWT tokens and create a custom token record.
    """
    refresh = RefreshToken.for_user(user)
    
    # Create custom token record
    token = CustomToken.create_token(
        user=user,
        refresh_token_key=str(refresh),
        device_info=None,
        ip_address=None
    )
    
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'token_key': token.key,
    }
