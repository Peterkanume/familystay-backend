from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import User

class Property(models.Model):
    """Property listing model"""
    
    class PropertyStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        BLOCKED = 'BLOCKED', 'Blocked'
    
    # Basic Information
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties', limit_choices_to={'role': 'HOST'})
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Location
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Property Details
    property_type = models.CharField(max_length=50)  # Apartment, House, Villa, etc.
    bedrooms = models.IntegerField(validators=[MinValueValidator(1)])
    bathrooms = models.DecimalField(max_digits=3, decimal_places=1)
    max_guests = models.IntegerField(validators=[MinValueValidator(1)])
    square_feet = models.IntegerField(null=True, blank=True)
    
    # Amenities (JSON field for flexibility)
    amenities = models.JSONField(default=dict)  # {"wifi": true, "kitchen": true, "pool": false}
    
    # Family-friendly features
    family_features = models.JSONField(default=dict)  # {"child_safe": true, "baby_cot": true}
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    cleaning_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Media
    featured_image = models.ImageField(upload_to='properties/featured/')
    
    # Status
    status = models.CharField(max_length=10, choices=PropertyStatus.choices, default=PropertyStatus.PENDING)
    is_available = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.IntegerField(default=0)
    
    class Meta:
        verbose_name_plural = "Properties"
        indexes = [
            models.Index(fields=['host', 'status']),
            models.Index(fields=['city', 'country']),
            models.Index(fields=['is_available']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0

class PropertyImage(models.Model):
    """Multiple images for a property"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='properties/gallery/')
    is_featured = models.BooleanField(default=False)
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_featured', 'uploaded_at']

class Availability(models.Model):
    """Property availability calendar"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='availability')
    date = models.DateField()
    is_available = models.BooleanField(default=True)
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Seasonal pricing
    notes = models.CharField(max_length=255, blank=True)
    
    class Meta:
        unique_together = ['property', 'date']
        indexes = [
            models.Index(fields=['property', 'date', 'is_available']),
        ]
    
    def __str__(self):
        return f"{self.property.title} - {self.date}"