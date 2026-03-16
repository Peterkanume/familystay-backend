from rest_framework import serializers
from .models import Property, PropertyImage, Availability


class PropertyImageSerializer(serializers.ModelSerializer):
    """Serializer for Property images"""
    
    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'is_featured', 'caption', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class AvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for Property availability"""
    
    class Meta:
        model = Availability
        fields = ['id', 'date', 'is_available', 'price_override', 'notes']
    
    def validate_date(self, value):
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("Can't set availability for past dates")
        return value


class PropertyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for property listings"""
    images = PropertyImageSerializer(many=True, read_only=True)
    host_name = serializers.CharField(source='host.get_full_name', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Property
        fields = ['id', 'title', 'city', 'country', 'property_type', 'bedrooms', 
                  'bathrooms', 'max_guests', 'base_price', 'featured_image', 'images',
                  'host_name', 'average_rating', 'is_available', 'status']


class PropertyDetailSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for property details"""
    images = PropertyImageSerializer(many=True, read_only=True)
    host = serializers.SerializerMethodField()
    average_rating = serializers.FloatField(read_only=True)
    total_reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = ['id', 'title', 'description', 'address', 'city', 'state', 'country', 
                  'zip_code', 'latitude', 'longitude', 'property_type', 'bedrooms', 
                  'bathrooms', 'max_guests', 'square_feet', 'amenities', 'family_features',
                  'base_price', 'cleaning_fee', 'service_fee', 'security_deposit',
                  'featured_image', 'images', 'host', 'status', 'is_available',
                  'average_rating', 'total_reviews', 'views_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'views_count', 'created_at', 'updated_at']
    
    def get_host(self, obj):
        return {
            'id': obj.host.id,
            'name': obj.host.get_full_name() or obj.host.username,
            'profile_picture': obj.host.profile_picture.url if obj.host.profile_picture else None
        }
    
    def get_total_reviews(self, obj):
        return obj.reviews.count()


class PropertyCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating properties"""
    
    class Meta:
        model = Property
        fields = ['title', 'description', 'address', 'city', 'state', 'country', 
                  'zip_code', 'latitude', 'longitude', 'property_type', 'bedrooms', 
                  'bathrooms', 'max_guests', 'square_feet', 'amenities', 'family_features',
                  'base_price', 'cleaning_fee', 'service_fee', 'security_deposit',
                  'featured_image', 'is_available']
    
    def validate(self, attrs):
        # Only hosts can create properties
        if self.context['request'].user.role != 'HOST':
            raise serializers.ValidationError("Only hosts can create properties")
        
        # Validate max_guests is at least 1
        if attrs.get('max_guests', 0) < 1:
            raise serializers.ValidationError({"max_guests": "Must be at least 1"})
        
        # Validate prices are not negative
        for field in ['base_price', 'cleaning_fee', 'service_fee', 'security_deposit']:
            if attrs.get(field, 0) < 0:
                raise serializers.ValidationError({field: "Cannot be negative"})
        
        return attrs


class PropertyImageUploadSerializer(serializers.Serializer):
    """Serializer for uploading property images"""
    images = serializers.ListField(
        child=serializers.ImageField(),
        allow_empty=False
    )
    
    def validate_images(self, images):
        max_size = 5 * 1024 * 1024  # 5MB
        allowed_extensions = ['jpg', 'jpeg', 'png', 'webp']
        
        for image in images:
            if image.size > max_size:
                raise serializers.ValidationError(f"Image {image.name} is too large. Max size is 5MB")
            
            ext = image.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(f"Extension {ext} not allowed. Allowed: {allowed_extensions}")
        
        return images


class AvailabilityBulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk availability updates"""
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    is_available = serializers.BooleanField()
    price_override = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    
    def validate(self, attrs):
        if attrs['end_date'] < attrs['start_date']:
            raise serializers.ValidationError({"end_date": "End date must be after start date"})
        return attrs
