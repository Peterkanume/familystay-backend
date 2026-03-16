from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg
from datetime import datetime, timedelta
from .models import Property, PropertyImage, Availability
from .serializers import (
    PropertyListSerializer, PropertyDetailSerializer, PropertyCreateUpdateSerializer,
    PropertyImageSerializer, AvailabilitySerializer, AvailabilityBulkUpdateSerializer
)
from apps.accounts.permissions import IsHost, IsAdmin, CanManageProperty


class PropertyListView(generics.ListAPIView):
    """Public endpoint to list properties with filters"""
    serializer_class = PropertyListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Property.objects.filter(
            status='APPROVED',
            is_available=True
        ).select_related('host').prefetch_related('images')
        
        # Filter by city
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        # Filter by country
        country = self.request.query_params.get('country')
        if country:
            queryset = queryset.filter(country__icontains=country)
        
        # Filter by property type
        property_type = self.request.query_params.get('property_type')
        if property_type:
            queryset = queryset.filter(property_type=property_type)
        
        # Filter by bedrooms
        bedrooms = self.request.query_params.get('bedrooms')
        if bedrooms:
            queryset = queryset.filter(bedrooms__gte=int(bedrooms))
        
        # Filter by bathrooms
        bathrooms = self.request.query_params.get('bathrooms')
        if bathrooms:
            queryset = queryset.filter(bathrooms__gte=float(bathrooms))
        
        # Filter by max guests
        max_guests = self.request.query_params.get('max_guests')
        if max_guests:
            queryset = queryset.filter(max_guests__gte=int(max_guests))
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(base_price__gte=float(min_price))
        if max_price:
            queryset = queryset.filter(base_price__lte=float(max_price))
        
        # Filter by amenities
        amenities = self.request.query_params.getlist('amenities')
        if amenities:
            for amenity in amenities:
                queryset = queryset.filter(amenities__contains=amenity)
        
        # Filter by family features
        family_features = self.request.query_params.getlist('family_features')
        if family_features:
            for feature in family_features:
                queryset = queryset.filter(family_features__contains=feature)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(city__icontains=search) |
                Q(address__icontains=search)
            )
        
        # Sort
        sort = self.request.query_params.get('sort', '-created_at')
        if sort in ['price', '-price', 'created_at', '-created_at', 'title', '-title']:
            queryset = queryset.order_by(sort)
        
        return queryset


class PropertyDetailView(generics.RetrieveAPIView):
    """Public endpoint to get property details"""
    queryset = Property.objects.all()
    serializer_class = PropertyDetailSerializer
    permission_classes = [permissions.AllowAny]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class PropertyAvailabilityView(APIView):
    """Get property availability for date range"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, pk):
        property = get_object_or_404(Property, pk=pk)
        
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            # Default to next 90 days
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=90)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get availability records
        availability = Availability.objects.filter(
            property=property,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        # Get booked dates from confirmed bookings
        booked_dates = []
        bookings = property.bookings.filter(
            booking_status__in=['PENDING', 'CONFIRMED'],
            check_in_date__lte=end_date,
            check_out_date__gte=start_date
        )
        
        for booking in bookings:
            current_date = booking.check_in_date
            while current_date < booking.check_out_date:
                booked_dates.append(current_date)
                current_date += timedelta(days=1)
        
        # Combine availability with booking data
        result = []
        current_date = start_date
        while current_date <= end_date:
            avail = availability.filter(date=current_date).first()
            is_booked = current_date in booked_dates
            
            result.append({
                'date': current_date.isoformat(),
                'is_available': avail.is_available if avail else not is_booked,
                'price_override': float(avail.price_override) if avail and avail.price_override else None,
                'is_booked': is_booked
            })
            current_date += timedelta(days=1)
        
        return Response(result)


class MyPropertiesView(generics.ListAPIView):
    """Host's own properties"""
    serializer_class = PropertyListSerializer
    permission_classes = [IsHost]
    
    def get_queryset(self):
        return Property.objects.filter(
            host=self.request.user
        ).prefetch_related('images')


class PropertyCreateView(generics.CreateAPIView):
    """Create a new property"""
    serializer_class = PropertyCreateUpdateSerializer
    permission_classes = [IsHost]
    
    def perform_create(self, serializer):
        serializer.save(host=self.request.user)


class PropertyUpdateView(generics.UpdateAPIView):
    """Update a property"""
    queryset = Property.objects.all()
    serializer_class = PropertyCreateUpdateSerializer
    permission_classes = [IsHost, CanManageProperty]
    
    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj


class PropertyDeleteView(generics.DestroyAPIView):
    """Delete a property"""
    queryset = Property.objects.all()
    permission_classes = [IsHost, CanManageProperty]
    
    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj


class PropertyImageUploadView(APIView):
    """Upload images for a property"""
    permission_classes = [IsHost, CanManageProperty]
    
    def post(self, request, pk):
        property = get_object_or_404(Property, pk=pk, host=request.user)
        
        images = request.FILES.getlist('images')
        if not images:
            return Response({'error': 'No images provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_images = []
        for image in images:
            property_image = PropertyImage.objects.create(
                property=property,
                image=image,
                is_featured=not property.images.exists()
            )
            uploaded_images.append(PropertyImageSerializer(property_image).data)
        
        return Response(uploaded_images, status=status.HTTP_201_CREATED)


class PropertyImageDeleteView(generics.DestroyAPIView):
    """Delete a property image"""
    queryset = PropertyImage.objects.all()
    permission_classes = [IsHost, CanManageProperty]
    
    def get_object(self):
        obj = super().get_object()
        # Check ownership
        if obj.property.host != self.request.user:
            self.permission_denied(self.request)
        return obj


class BulkAvailabilityUpdateView(APIView):
    """Bulk update availability for a property"""
    permission_classes = [IsHost, CanManageProperty]
    
    def post(self, request, pk):
        property = get_object_or_404(Property, pk=pk, host=request.user)
        
        serializer = AvailabilityBulkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']
        is_available = serializer.validated_data['is_available']
        price_override = serializer.validated_data.get('price_override')
        
        # Update/create availability records
        current_date = start_date
        updated_count = 0
        while current_date <= end_date:
            availability, created = Availability.objects.update_or_create(
                property=property,
                date=current_date,
                defaults={
                    'is_available': is_available,
                    'price_override': price_override
                }
            )
            updated_count += 1
            current_date += timedelta(days=1)
        
        return Response({
            'message': f'Updated {updated_count} dates',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'is_available': is_available
        })


# Admin endpoints
class ApprovePropertyView(APIView):
    """Approve a property (Admin only)"""
    permission_classes = [IsAdmin]
    
    def post(self, request, pk):
        property = get_object_or_404(Property, pk=pk)
        property.status = 'APPROVED'
        property.save(update_fields=['status'])
        
        return Response({'message': 'Property approved', 'status': property.status})


class RejectPropertyView(APIView):
    """Reject a property (Admin only)"""
    permission_classes = [IsAdmin]
    
    def post(self, request, pk):
        property = get_object_or_404(Property, pk=pk)
        property.status = 'REJECTED'
        property.save(update_fields=['status'])
        
        return Response({'message': 'Property rejected', 'status': property.status})


class BlockPropertyView(APIView):
    """Block a property (Admin only)"""
    permission_classes = [IsAdmin]
    
    def post(self, request, pk):
        property = get_object_or_404(Property, pk=pk)
        property.status = 'BLOCKED'
        property.is_available = False
        property.save(update_fields=['status', 'is_available'])
        
        return Response({'message': 'Property blocked', 'status': property.status})
