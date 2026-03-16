from decimal import Decimal

from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import Booking, BookingHistory, GuestInfo
from apps.properties.models import Property, Availability


class GuestInfoSerializer(serializers.ModelSerializer):
    """Serializer for guest information"""
    
    class Meta:
        model = GuestInfo
        fields = ['id', 'full_name', 'email', 'phone', 'id_type', 'id_number',
                  'emergency_contact_name', 'emergency_contact_phone']
        read_only_fields = ['id']


class BookingHistorySerializer(serializers.ModelSerializer):
    """Serializer for booking history"""
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    
    class Meta:
        model = BookingHistory
        fields = ['id', 'changed_by_name', 'changed_at', 'field_name', 'old_value', 'new_value', 'action']
        read_only_fields = fields


class BookingSerializer(serializers.ModelSerializer):
    """Read-only serializer for bookings"""
    guest = serializers.SerializerMethodField()
    listing = serializers.SerializerMethodField()
    guest_info = GuestInfoSerializer(read_only=True)
    
    class Meta:
        model = Booking
        fields = ['id', 'booking_reference', 'guest', 'listing', 'check_in_date', 'check_out_date',
                  'number_of_guests', 'number_of_children', 'special_requests', 'nightly_price',
                  'total_nights', 'subtotal', 'cleaning_fee', 'service_fee', 'tax_amount', 'total_amount',
                  'booking_status', 'payment_status', 'cancellation_reason', 'cancelled_at',
                  'created_at', 'updated_at', 'guest_info']
        read_only_fields = fields
    
    def get_guest(self, obj):
        return {
            'id': obj.guest.id,
            'name': obj.guest.get_full_name() or obj.guest.username,
            'email': obj.guest.email,
            'phone': obj.guest.phone_number
        }
    
    def get_listing(self, obj):
        return {
            'id': obj.listing.id,
            'title': obj.listing.title,
            'address': obj.listing.address,
            'city': obj.listing.city,
            'featured_image': obj.listing.featured_image.url if obj.listing.featured_image else None
        }


class BookingCreateSerializer(serializers.Serializer):
    """Serializer for creating bookings with validation"""
    property_id = serializers.IntegerField()
    check_in_date = serializers.DateField()
    check_out_date = serializers.DateField()
    number_of_guests = serializers.IntegerField(min_value=1)
    number_of_children = serializers.IntegerField(min_value=0, default=0)
    special_requests = serializers.CharField(required=False, allow_blank=True)
    
    # Guest info
    guest_full_name = serializers.CharField(max_length=100)
    guest_email = serializers.EmailField()
    guest_phone = serializers.CharField(max_length=20)
    guest_id_type = serializers.CharField(max_length=50, required=False, allow_blank=True)
    guest_id_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    emergency_contact_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    emergency_contact_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    def validate_check_in_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Check-in date cannot be in the past")
        return value
    
    def validate(self, attrs):
        check_in = attrs.get('check_in_date')
        check_out = attrs.get('check_out_date')
        
        if check_out <= check_in:
            raise serializers.ValidationError({"check_out_date": "Check-out date must be after check-in date"})
        
        # Check minimum stay (1 night)
        duration = (check_out - check_in).days
        if duration < 1:
            raise serializers.ValidationError({"check_out_date": "Minimum stay is 1 night"})
        
        # Check maximum stay (90 days)
        if duration > 90:
            raise serializers.ValidationError({"check_out_date": "Maximum stay is 90 nights"})
        
        return attrs
    
    def validate_property_id(self, value):
        try:
            property = Property.objects.get(id=value)
        except Property.DoesNotExist:
            raise serializers.ValidationError("Property not found")
        
        if property.status != 'APPROVED':
            raise serializers.ValidationError("Property is not available for booking")
        
        if not property.is_available:
            raise serializers.ValidationError("Property is not currently available")
        
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        property_id = validated_data.pop('property_id')
        property = Property.objects.get(id=property_id)
        
        # Calculate pricing
        check_in = validated_data['check_in_date']
        check_out = validated_data['check_out_date']
        nights = (check_out - check_in).days
        
        # Get seasonal pricing if available
        nightly_price = property.base_price
        for day in range(nights):
            date = check_in + timedelta(days=day)
            try:
                availability = Availability.objects.get(property=property, date=date)
                if availability.price_override:
                    nightly_price = availability.price_override
                    break
            except Availability.DoesNotExist:
                pass
        
        subtotal = nightly_price * nights
        cleaning_fee = property.cleaning_fee
        service_fee = property.service_fee
        tax_rate = Decimal(0.16)  # 16% VAT
        tax_amount = (subtotal + cleaning_fee + service_fee) * tax_rate
        total_amount = subtotal + cleaning_fee + service_fee + tax_amount
        
        # Check property capacity
        total_guests = validated_data.get('number_of_guests', 0) + validated_data.get('number_of_children', 0)
        if total_guests > property.max_guests:
            raise serializers.ValidationError({
                'number_of_guests': f"Property can accommodate maximum {property.max_guests} guests"
            })
        
        # Check availability
        booked_dates = Booking.objects.filter(
            listing=property,
            booking_status__in=['PENDING', 'CONFIRMED'],
            check_in_date__lt=check_out,
            check_out_date__gt=check_in
        ).exists()
        
        if booked_dates:
            raise serializers.ValidationError("Property is not available for selected dates")
        
        unavailable_dates = Availability.objects.filter(
            property=property,
            date__gte=check_in,
            date__lt=check_out,
            is_available=False
        ).exists()
        
        if unavailable_dates:
            raise serializers.ValidationError("Some dates are not available")
        
        # Create booking
        booking = Booking.objects.create(
            guest=user,
            listing=property,
            check_in_date=check_in,
            check_out_date=check_out,
            number_of_guests=validated_data['number_of_guests'],
            number_of_children=validated_data.get('number_of_children', 0),
            special_requests=validated_data.get('special_requests', ''),
            nightly_price=nightly_price,
            total_nights=nights,
            subtotal=subtotal,
            cleaning_fee=cleaning_fee,
            service_fee=service_fee,
            tax_amount=tax_amount,
            total_amount=total_amount
        )
        
        # Create guest info
        GuestInfo.objects.create(
            booking=booking,
            full_name=validated_data['guest_full_name'],
            email=validated_data['guest_email'],
            phone=validated_data['guest_phone'],
            id_type=validated_data.get('guest_id_type', ''),
            id_number=validated_data.get('guest_id_number', ''),
            emergency_contact_name=validated_data.get('emergency_contact_name', ''),
            emergency_contact_phone=validated_data.get('emergency_contact_phone', '')
        )
        
        # Create history
        BookingHistory.objects.create(
            booking=booking,
            changed_by=user,
            action='CREATE',
            field_name='booking',
            new_value='Booking created'
        )
        
        return booking


class BookingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating bookings"""
    
    class Meta:
        model = Booking
        fields = ['check_in_date', 'check_out_date', 'number_of_guests', 'number_of_children', 'special_requests']
    
    def validate(self, attrs):
        booking = self.instance
        
        # Only allow updates for pending bookings
        if booking.booking_status != 'PENDING':
            raise serializers.ValidationError("Can only update pending bookings")
        
        # If dates are being changed, validate them
        if 'check_in_date' in attrs or 'check_out_date' in attrs:
            check_in = attrs.get('check_in_date', booking.check_in_date)
            check_out = attrs.get('check_out_date', booking.check_out_date)
            
            if check_out <= check_in:
                raise serializers.ValidationError({"check_out_date": "Check-out date must be after check-in date"})
        
        return attrs


class BookingCancelSerializer(serializers.Serializer):
    """Serializer for cancelling bookings"""
    cancellation_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        booking = self.instance
        
        if booking.booking_status in ['CANCELLED', 'COMPLETED']:
            raise serializers.ValidationError("Cannot cancel this booking")
        
        # Calculate refund based on cancellation policy
        days_until_checkin = (booking.check_in_date - timezone.now().date()).days
        
        if days_until_checkin >= 7:
            refund_percentage = 1.0  # Full refund
        elif days_until_checkin >= 3:
            refund_percentage = 0.5  # 50% refund
        elif days_until_checkin >= 1:
            refund_percentage = 0.25  # 25% refund
        else:
            refund_percentage = 0  # No refund
        
        attrs['refund_percentage'] = refund_percentage
        return attrs
