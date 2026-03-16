from django.urls import path
from .views import (
    CreateBookingView, MyBookingsView, BookingDetailView,
    CancelBookingView, ModifyBookingView, HostBookingsView,
    UpdateBookingStatusView, BookingHistoryView
)

urlpatterns = [
    # Guest endpoints
    path('create/', CreateBookingView.as_view(), name='create_booking'),
    path('my-bookings/', MyBookingsView.as_view(), name='my_bookings'),
    path('<int:pk>/', BookingDetailView.as_view(), name='booking_detail'),
    path('<int:pk>/cancel/', CancelBookingView.as_view(), name='cancel_booking'),
    path('<int:pk>/modify/', ModifyBookingView.as_view(), name='modify_booking'),
    path('<int:pk>/history/', BookingHistoryView.as_view(), name='booking_history'),
    
    # Host endpoints
    path('host/bookings/', HostBookingsView.as_view(), name='host_bookings'),
    path('host/<int:pk>/update-status/', UpdateBookingStatusView.as_view(), name='update_booking_status'),
]
