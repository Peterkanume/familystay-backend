from rest_framework import serializers
from django.utils import timezone
from .models import Payment, Payout, TransactionLog


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    payer_name = serializers.CharField(source='payer.get_full_name', read_only=True)
    recipient_name = serializers.CharField(source='recipient.get_full_name', read_only=True)
    booking_reference = serializers.CharField(source='booking.booking_reference', read_only=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'transaction_id', 'booking_reference', 'payer_name', 'recipient_name',
                  'payment_method', 'amount', 'currency', 'status', 'provider_reference',
                  'description', 'error_message', 'created_at', 'updated_at', 'completed_at']
        read_only_fields = fields


class PaymentInitiateSerializer(serializers.Serializer):
    """Serializer for initiating M-Pesa payment"""
    booking_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(choices=Payment.PaymentMethod.choices)
    phone_number = serializers.CharField(max_length=15)
    
    def validate_booking_id(self, value):
        from apps.bookings.models import Booking
        try:
            booking = Booking.objects.get(id=value)
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found")
        
        if booking.payment_status == 'PAID':
            raise serializers.ValidationError("Booking is already paid")
        
        if booking.booking_status == 'CANCELLED':
            raise serializers.ValidationError("Cannot pay for cancelled booking")
        
        return value
    
    def validate_phone_number(self, value):
        # Remove any spaces or dashes
        phone = value.replace(' ', '').replace('-', '')
        
        # Kenyan phone number validation
        if phone.startswith('+254'):
            phone = phone[1:]
        elif phone.startswith('0'):
            phone = '254' + phone[1:]
        
        if not phone.startswith('254') or len(phone) != 12:
            raise serializers.ValidationError("Invalid phone number format. Use format: 254XXXXXXXXX")
        
        return phone


class PaymentVerifySerializer(serializers.Serializer):
    """Serializer for verifying payment status"""
    transaction_id = serializers.CharField(max_length=100)


class PayoutSerializer(serializers.ModelSerializer):
    """Serializer for Payout model"""
    host_name = serializers.CharField(source='host.get_full_name', read_only=True)
    
    class Meta:
        model = Payout
        fields = ['id', 'reference', 'host_name', 'amount', 'currency', 'status', 
                  'payout_method', 'account_details', 'requested_at', 'processed_at']
        read_only_fields = fields


class PayoutRequestSerializer(serializers.Serializer):
    """Serializer for requesting a payout"""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=1000)
    payout_method = serializers.ChoiceField(choices=Payout.PayoutMethod.choices)
    
    # M-Pesa details
    phone_number = serializers.CharField(max_length=15, required=False)
    
    # Bank details
    bank_name = serializers.CharField(max_length=100, required=False)
    account_number = serializers.CharField(max_length=50, required=False)
    account_name = serializers.CharField(max_length=100, required=False)
    
    # PayPal
    paypal_email = serializers.EmailField(required=False)
    
    def validate(self, attrs):
        payout_method = attrs.get('payout_method')
        
        if payout_method == 'MPESA':
            if not attrs.get('phone_number'):
                raise serializers.ValidationError({"phone_number": "Phone number is required for M-Pesa"})
        elif payout_method == 'BANK':
            if not all([attrs.get('bank_name'), attrs.get('account_number'), attrs.get('account_name')]):
                raise serializers.ValidationError({"bank": "Bank details are required for bank transfer"})
        elif payout_method == 'PAYPAL':
            if not attrs.get('paypal_email'):
                raise serializers.ValidationError({"paypal_email": "PayPal email is required"})
        
        return attrs


class TransactionLogSerializer(serializers.ModelSerializer):
    """Serializer for TransactionLog model"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = TransactionLog
        fields = ['id', 'transaction_type', 'transaction_id', 'user_name', 'amount',
                  'status', 'request_data', 'response_data', 'ip_address', 'created_at']
        read_only_fields = fields
