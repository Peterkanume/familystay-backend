from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Review, HostReview, ReviewReport
from .serializers import (
    ReviewSerializer, ReviewCreateSerializer, ReviewUpdateSerializer,
    ReviewReplySerializer, HostReviewSerializer, HostReviewCreateSerializer,
    ReviewReportSerializer
)
from apps.accounts.permissions import IsGuest, IsHost, CanManageBooking, IsAdmin


class CreateReviewView(generics.CreateAPIView):
    """Create a review for a booking"""
    serializer_class = ReviewCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsGuest]
    
    def create(self, request, *args, **kwargs):
        serializer = ReviewCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        booking_id = serializer.validated_data['booking_id']
        booking = get_object_or_404(Booking, id=booking_id)
        
        review = Review.objects.create(
            booking=booking,
            guest=request.user,
            property=booking.listing,
            host=booking.listing.host,
            overall_rating=serializer.validated_data['overall_rating'],
            cleanliness_rating=serializer.validated_data['cleanliness_rating'],
            communication_rating=serializer.validated_data['communication_rating'],
            checkin_rating=serializer.validated_data['checkin_rating'],
            accuracy_rating=serializer.validated_data['accuracy_rating'],
            location_rating=serializer.validated_data['location_rating'],
            value_rating=serializer.validated_data['value_rating'],
            child_friendly_rating=serializer.validated_data.get('child_friendly_rating'),
            safety_rating=serializer.validated_data.get('safety_rating'),
            comment=serializer.validated_data['comment'],
            images=serializer.validated_data.get('images', [])
        )
        
        return Response(
            ReviewSerializer(review).data,
            status=status.HTTP_201_CREATED
        )


class PropertyReviewsView(generics.ListAPIView):
    """Get reviews for a property"""
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        property_id = self.kwargs['property_id']
        queryset = Review.objects.filter(
            property_id=property_id,
            is_approved=True
        ).select_related('guest', 'property', 'host')
        
        # Filter by rating
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(overall_rating__gte=min_rating)
        
        return queryset


class UpdateReviewView(generics.UpdateAPIView):
    """Update a review"""
    serializer_class = ReviewUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Review.objects.filter(guest=self.request.user)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check if within 48 hours
        time_diff = timezone.now() - instance.created_at
        if time_diff.total_seconds() > 48 * 3600:
            return Response(
                {'error': 'Reviews can only be updated within 48 hours'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().update(request, *args, **kwargs)


class DeleteReviewView(generics.DestroyAPIView):
    """Delete a review"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Review.objects.filter(guest=self.request.user)


class HostReplyView(APIView):
    """Host replies to a review"""
    permission_classes = [permissions.IsAuthenticated, IsHost]
    
    def post(self, request, review_id):
        review = get_object_or_404(Review, id=review_id, property__host=request.user)
        
        serializer = ReviewReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        review.host_reply = serializer.validated_data['host_reply']
        review.host_replied_at = timezone.now()
        review.save(update_fields=['host_reply', 'host_replied_at'])
        
        return Response(ReviewSerializer(review).data)


class ReportReviewView(APIView):
    """Report a review"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, review_id):
        review = get_object_or_404(Review, id=review_id)
        
        # Check if already reported
        if ReviewReport.objects.filter(review=review, reported_by=request.user).exists():
            return Response(
                {'error': 'You have already reported this review'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ReviewReportSerializer(
            data=request.data,
            context={'request': request, 'review_id': review_id}
        )
        serializer.is_valid(raise_exception=True)
        
        report = ReviewReport.objects.create(
            review=review,
            reported_by=request.user,
            reason=serializer.validated_data['reason'],
            description=serializer.validated_data['description']
        )
        
        # Mark review as reported
        review.is_reported = True
        review.save(update_fields=['is_reported'])
        
        return Response({'message': 'Review reported successfully'})


class ModerateReviewView(APIView):
    """Admin moderates a review"""
    permission_classes = [IsAdmin]
    
    def post(self, request, review_id):
        review = get_object_or_404(Review, id=review_id)
        
        action = request.data.get('action')
        
        if action == 'approve':
            review.is_approved = True
            review.is_reported = False
            review.save(update_fields=['is_approved', 'is_reported'])
            
            # Resolve any reports
            ReviewReport.objects.filter(review=review).update(
                status='DISMISSED',
                resolved_by=request.user,
                resolved_at=timezone.now()
            )
            
            return Response({'message': 'Review approved'})
        
        elif action == 'remove':
            review.delete()
            return Response({'message': 'Review removed'})
        
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)


# Import models
from apps.bookings.models import Booking
