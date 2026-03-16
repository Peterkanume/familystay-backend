from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models
from .models import Booking, BookingHistory, GuestInfo
from .serializers import (
    BookingSerializer, BookingCreateSerializer, BookingUpdateSerializer,
    BookingCancelSerializer, BookingHistorySerializer
)
from apps.accounts.permissions import IsGuest, IsHost, CanManageBooking, IsAdmin


class CreateBookingView(generics.CreateAPIView):
    """Create a new booking"""
    serializer_class = BookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        
        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_201_CREATED
        )


class MyBookingsView(generics.ListAPIView):
    """Get current user's bookings"""
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Booking.objects.filter(guest=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(booking_status=status_filter)
        
        # Filter by payment status
        payment_status = self.request.query_params.get('payment_status')
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        
        # Filter by date range
        check_in_after = self.request.query_params.get('check_in_after')
        check_in_before = self.request.query_params.get('check_in_before')
        
        if check_in_after:
            queryset = queryset.filter(check_in_date__gte=check_in_after)
        if check_in_before:
            queryset = queryset.filter(check_in_date__lte=check_in_before)
        
        return queryset.select_related('listing', 'guest').prefetch_related('listing__images')


class BookingDetailView(generics.RetrieveAPIView):
    """Get booking details"""
    serializer_class = BookingSerializer
    permission_classes = [CanManageBooking]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN' or user.is_superuser:
            return Booking.objects.all()
        return Booking.objects.filter(
            models.Q(guest=user) | models.Q(listing__host=user)
        )


class CancelBookingView(APIView):
    """Cancel a booking"""
    permission_classes = [CanManageBooking]
    
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        
        # Check permissions
        if not (request.user == booking.guest or 
                request.user == booking.listing.host or 
                request.user.role == 'ADMIN' or 
                request.user.is_superuser):
            return Response(
                {'error': 'You cannot cancel this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.booking_status in ['CANCELLED', 'COMPLETED']:
            return Response(
                {'error': 'Cannot cancel this booking'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = BookingCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update booking status
        booking.booking_status = 'CANCELLED'
        booking.cancellation_reason = serializer.validated_data.get('cancellation_reason', '')
        booking.cancelled_at = timezone.now()
        booking.cancelled_by = request.user
        booking.save(update_fields=['booking_status', 'cancellation_reason', 'cancelled_at', 'cancelled_by'])
        
        # Create history record
        BookingHistory.objects.create(
            booking=booking,
            changed_by=request.user,
            action='CANCEL',
            field_name='booking_status',
            old_value='PENDING/CONFIRMED',
            new_value='CANCELLED'
        )
        
        return Response({
            'message': 'Booking cancelled successfully',
            'booking': BookingSerializer(booking).data
        })


class ModifyBookingView(APIView):
    """Modify a booking"""
    permission_classes = [CanManageBooking]
    
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        
        if booking.booking_status != 'PENDING':
            return Response(
                {'error': 'Can only modify pending bookings'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if request.user != booking.guest:
            return Response(
                {'error': 'Only the guest can modify the booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BookingUpdateSerializer(booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Create history record
        BookingHistory.objects.create(
            booking=booking,
            changed_by=request.user,
            action='MODIFY',
            field_name='booking',
            new_value='Booking modified'
        )
        
        return Response(BookingSerializer(booking).data)


class HostBookingsView(generics.ListAPIView):
    """Get host's bookings for their properties"""
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Booking.objects.filter(
            listing__host=self.request.user
        ).select_related('listing', 'guest')
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(booking_status=status_filter)
        
        # Filter by payment status
        payment_status = self.request.query_params.get('payment_status')
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        
        # Filter by date
        check_in_after = self.request.query_params.get('check_in_after')
        if check_in_after:
            queryset = queryset.filter(check_in_date__gte=check_in_after)
        
        return queryset


class UpdateBookingStatusView(APIView):
    """Host updates booking status"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        
        # Check if host owns the property
        if request.user != booking.listing.host:
            return Response(
                {'error': 'You can only update bookings for your properties'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get('status')
        if new_status not in ['CONFIRMED', 'CANCELLED']:
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = booking.booking_status
        booking.booking_status = new_status
        booking.save(update_fields=['booking_status'])
        
        # Create history
        BookingHistory.objects.create(
            booking=booking,
            changed_by=request.user,
            action='STATUS_UPDATE',
            field_name='booking_status',
            old_value=old_status,
            new_value=new_status
        )
        
        return Response(BookingSerializer(booking).data)


class BookingHistoryView(generics.ListAPIView):
    """Get booking history"""
    serializer_class = BookingHistorySerializer
    permission_classes = [CanManageBooking]
    
    def get_queryset(self):
        booking_pk = self.kwargs.get('pk')
        booking = get_object_or_404(Booking, pk=booking_pk)
        
        # The CanManageBooking permission should already handle authorization
        return BookingHistory.objects.filter(booking=booking)