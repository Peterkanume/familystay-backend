from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from apps.accounts.models import User
from apps.properties.models import Property

class Booking(models.Model):
    """Booking model for reservations"""
    
    class BookingStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        COMPLETED = 'COMPLETED', 'Completed'
        NO_SHOW = 'NO_SHOW', 'No Show'
        REFUNDED = 'REFUNDED', 'Refunded'
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'
        PARTIALLY_REFUNDED = 'PARTIAL', 'Partially Refunded'
    
    # Relationships
    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', limit_choices_to={'role': 'GUEST'})
    listing = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')
    
    # Booking details
    booking_reference = models.CharField(max_length=20, unique=True, editable=False)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    number_of_guests = models.IntegerField(validators=[MinValueValidator(1)])
    number_of_children = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    special_requests = models.TextField(blank=True)
    
    # Pricing breakdown
    nightly_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_nights = models.IntegerField(validators=[MinValueValidator(1)])
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)  # nightly_price * total_nights
    cleaning_fee = models.DecimalField(max_digits=10, decimal_places=2)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)  # subtotal + all fees + tax
    
    # Status
    booking_status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    
    # Cancellation
    cancellation_reason = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_bookings')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking_reference']),
            models.Index(fields=['guest', 'booking_status']),
            models.Index(fields=['listing', 'check_in_date', 'check_out_date']),
            models.Index(fields=['booking_status', 'payment_status']),
        ]
    
    def __str__(self):
        return f"Booking {self.booking_reference} - {self.guest.username}"
    
    def save(self, *args, **kwargs):
        if not self.booking_reference:
            # Generate unique booking reference (e.g., FAM-2024-00001)
            last_booking = Booking.objects.order_by('-id').first()
            last_id = last_booking.id if last_booking else 0
            year = timezone.now().year
            self.booking_reference = f"FAM-{year}-{last_id + 1:05d}"
        super().save(*args, **kwargs)
    
    @property
    def duration(self):
        """Calculate duration of stay in days"""
        return (self.check_out_date - self.check_in_date).days
    
    @property
    def is_active(self):
        """Check if booking is currently active"""
        today = timezone.now().date()
        return (self.booking_status == 'CONFIRMED' and 
                self.check_in_date <= today <= self.check_out_date)

class BookingHistory(models.Model):
    """Track all changes to bookings for audit purposes"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='history')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    field_name = models.CharField(max_length=50)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    action = models.CharField(max_length=50)  # CREATE, UPDATE, CANCEL, etc.
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name_plural = "Booking histories"
    
    def __str__(self):
        return f"{self.booking.booking_reference} - {self.action} at {self.changed_at}"

class GuestInfo(models.Model):
    """Additional guest information for a booking"""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='guest_info')
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    id_type = models.CharField(max_length=50, blank=True)  # Passport, National ID, etc.
    id_number = models.CharField(max_length=50, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return f"Guest info for {self.booking.booking_reference}"