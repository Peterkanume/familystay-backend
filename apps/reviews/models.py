from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import User
from apps.properties.models import Property
from apps.bookings.models import Booking

class Review(models.Model):
    """Review model for guest feedback"""
    
    # Relationships
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given', limit_choices_to={'role': 'GUEST'})
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reviews')
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received', limit_choices_to={'role': 'HOST'})
    
    # Ratings (1-5 scale)
    overall_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    cleanliness_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    communication_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    checkin_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    accuracy_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    location_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    value_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # Family-specific ratings
    child_friendly_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    safety_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    
    # Review content
    comment = models.TextField()
    host_reply = models.TextField(blank=True)
    host_replied_at = models.DateTimeField(null=True, blank=True)
    
    # Images (optional)
    images = models.JSONField(default=list)  # List of image URLs
    
    # Status
    is_approved = models.BooleanField(default=False)  # Admin approval
    is_reported = models.BooleanField(default=False)
    report_reason = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['property', 'created_at']),
            models.Index(fields=['guest', 'created_at']),
            models.Index(fields=['overall_rating']),
        ]
    
    def __str__(self):
        return f"Review by {self.guest.username} for {self.property.title}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update property average rating
        from django.db.models import Avg
        avg_rating = Review.objects.filter(property=self.property).aggregate(Avg('overall_rating'))
        # You could store this in a denormalized field on Property if needed

class HostReview(models.Model):
    """Reviews that guests can leave for hosts"""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='host_review')
    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='host_reviews_given')
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='host_reviews_received')
    
    communication_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    friendliness_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    accuracy_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Host review by {self.guest.username} for {self.host.username}"

class ReviewReport(models.Model):
    """Track reported reviews for admin moderation"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    class Reason(models.TextChoices):
        SPAM = "spam", "Spam"
        ABUSE = "abuse", "Abusive Content"
        OFFENSIVE = "offensive", "Offensive Language"
        OTHER = "other", "Other"

    reason = models.CharField(
        max_length=20,
        choices=Reason.choices
    )
    description = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('REVIEWED', 'Reviewed'),
        ('DISMISSED', 'Dismissed'),
        ('ACTION_TAKEN', 'Action taken'),
    ], default='PENDING')
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_reports')
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['review', 'status']),
        ]