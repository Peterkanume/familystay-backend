from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Custom user model with role-based access"""
    
    class Role(models.TextChoices):
        GUEST = 'GUEST', 'Guest'
        HOST = 'HOST', 'Host'
        ADMIN = 'ADMIN', 'Admin'
    
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.GUEST
    )
    phone_number = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} - {self.role}"
    
    @property
    def is_guest(self):
        return self.role == self.Role.GUEST
    
    @property
    def is_host(self):
        return self.role == self.Role.HOST
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser