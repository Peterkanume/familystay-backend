from django.db import models
from django.core.validators import MinValueValidator
from apps.accounts.models import User
from apps.bookings.models import Booking

class Payment(models.Model):
    """Payment model for transactions"""
    
    class PaymentMethod(models.TextChoices):
        MPESA = 'MPESA', 'M-Pesa'
        CARD = 'CARD', 'Credit/Debit Card'
        PAYPAL = 'PAYPAL', 'PayPal'
        BANK = 'BANK', 'Bank Transfer'
    
    class PaymentStatus(models.TextChoices):
        INITIATED = 'INITIATED', 'Initiated'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'
        PARTIALLY_REFUNDED = 'PARTIAL', 'Partially Refunded'
    
    # Relationships
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_made')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_received')
    
    # Payment details
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='KES')
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.INITIATED)
    
    # Payment provider details
    provider_reference = models.CharField(max_length=200, blank=True)  # M-Pesa transaction ID, Stripe payment intent ID
    provider_response = models.JSONField(default=dict)  # Store raw response from payment provider
    
    # Metadata
    description = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['payer', 'status']),
            models.Index(fields=['booking', 'status']),
        ]
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.amount} {self.currency}"

class Payout(models.Model):
    """Payout model for hosts to withdraw earnings"""
    
    class PayoutStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
    
    class PayoutMethod(models.TextChoices):
        MPESA = 'MPESA', 'M-Pesa'
        BANK = 'BANK', 'Bank Transfer'
        PAYPAL = 'PAYPAL', 'PayPal'
    
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payouts', limit_choices_to={'role': 'HOST'})
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    status = models.CharField(max_length=20, choices=PayoutStatus.choices, default=PayoutStatus.PENDING)
    payout_method = models.CharField(max_length=20, choices=PayoutMethod.choices)
    
    # Payout details
    account_details = models.JSONField()  # Store account number, bank details, etc. (encrypted in production)
    reference = models.CharField(max_length=100, unique=True)
    provider_response = models.JSONField(default=dict)
    
    # Which bookings are included in this payout
    bookings = models.ManyToManyField(Booking, related_name='payouts')
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['host', 'status']),
            models.Index(fields=['reference']),
        ]
    
    def __str__(self):
        return f"Payout {self.reference} - {self.host.username} - {self.amount}"

class TransactionLog(models.Model):
    """Audit log for all financial transactions"""
    transaction_type = models.CharField(max_length=50)  # PAYMENT, REFUND, PAYOUT, etc.
    transaction_id = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)
    request_data = models.JSONField(default=dict)
    response_data = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['user', 'created_at']),
        ]