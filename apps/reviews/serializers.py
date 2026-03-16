from rest_framework import serializers
from .models import Review, HostReview, ReviewReport
from apps.accounts.serializers import UserSerializer


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model"""
    guest = UserSerializer(read_only=True)
    property_title = serializers.CharField(source='property.title', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'guest', 'property', 'property_title', 'host', 'overall_rating',
                  'cleanliness_rating', 'communication_rating', 'checkin_rating', 'accuracy_rating',
                  'location_rating', 'value_rating', 'child_friendly_rating', 'safety_rating',
                  'comment', 'host_reply', 'host_replied_at', 'images', 'is_approved',
                  'is_reported', 'created_at', 'updated_at']
        read_only_fields = fields


class ReviewCreateSerializer(serializers.Serializer):
    """Serializer for creating a review"""
    booking_id = serializers.IntegerField()
    
    # Ratings (all required)
    overall_rating = serializers.IntegerField(min_value=1, max_value=5)
    cleanliness_rating = serializers.IntegerField(min_value=1, max_value=5)
    communication_rating = serializers.IntegerField(min_value=1, max_value=5)
    checkin_rating = serializers.IntegerField(min_value=1, max_value=5)
    accuracy_rating = serializers.IntegerField(min_value=1, max_value=5)
    location_rating = serializers.IntegerField(min_value=1, max_value=5)
    value_rating = serializers.IntegerField(min_value=1, max_value=5)
    
    # Family-specific ratings (optional)
    child_friendly_rating = serializers.IntegerField(min_value=1, max_value=5, required=False)
    safety_rating = serializers.IntegerField(min_value=1, max_value=5, required=False)
    
    # Content
    comment = serializers.CharField(min_length=10, max_length=2000)
    images = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        default=list
    )
    
    def validate_booking_id(self, value):
        from apps.bookings.models import Booking
        try:
            booking = Booking.objects.get(id=value)
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found")
        
        if booking.booking_status != 'COMPLETED':
            raise serializers.ValidationError("Can only review completed bookings")
        
        if booking.guest != self.context['request'].user:
            raise serializers.ValidationError("You can only review your own bookings")
        
        # Check if already reviewed
        if hasattr(booking, 'review'):
            raise serializers.ValidationError("You have already reviewed this booking")
        
        return value


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a review"""
    
    class Meta:
        model = Review
        fields = ['comment', 'images']
    
    def validate(self, attrs):
        review = self.instance
        
        # Only allow updating within 48 hours
        from django.utils import timezone
        time_diff = timezone.now() - review.created_at
        if time_diff.total_seconds() > 48 * 3600:
            raise serializers.ValidationError("Reviews can only be updated within 48 hours")
        
        return attrs


class ReviewReplySerializer(serializers.Serializer):
    """Serializer for host reply to review"""
    host_reply = serializers.CharField(max_length=1000)
    
    def validate_host_reply(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Reply must be at least 5 characters")
        return value


class HostReviewSerializer(serializers.ModelSerializer):
    """Serializer for HostReview model"""
    guest = UserSerializer(read_only=True)
    
    class Meta:
        model = HostReview
        fields = ['id', 'guest', 'host', 'communication_rating', 'friendliness_rating',
                  'accuracy_rating', 'comment', 'created_at']
        read_only_fields = fields


class HostReviewCreateSerializer(serializers.Serializer):
    """Serializer for creating host review"""
    booking_id = serializers.IntegerField()
    communication_rating = serializers.IntegerField(min_value=1, max_value=5)
    friendliness_rating = serializers.IntegerField(min_value=1, max_value=5)
    accuracy_rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(min_length=10, max_length=1000)
    
    def validate_booking_id(self, value):
        from apps.bookings.models import Booking
        try:
            booking = Booking.objects.get(id=value)
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found")
        
        if booking.booking_status != 'COMPLETED':
            raise serializers.ValidationError("Can only review completed bookings")
        
        if booking.guest != self.context['request'].user:
            raise serializers.ValidationError("You can only review your own bookings")
        
        if hasattr(booking, 'host_review'):
            raise serializers.ValidationError("You have already reviewed this host")
        
        return value


class ReviewReportSerializer(serializers.Serializer):
    """Serializer for reporting a review"""
    reason = serializers.ChoiceField(choices=ReviewReport.Reason.choices)
    description = serializers.CharField(min_length=20, max_length=500)
    
    def validate(self, attrs):
        review_id = self.context.get('review_id')
        user = self.context['request'].user
        
        # Check if already reported
        if ReviewReport.objects.filter(review_id=review_id, reported_by=user).exists():
            raise serializers.ValidationError("You have already reported this review")
        
        return attrs
