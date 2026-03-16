from django.contrib import admin
from .models import Booking, BookingHistory, GuestInfo


class GuestInfoInline(admin.TabularInline):
    model = GuestInfo
    extra = 0
    readonly_fields = ['full_name', 'email', 'phone', 'id_type', 'id_number']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Booking Admin"""
    list_display = ['booking_reference', 'guest', 'listing', 'check_in_date', 'check_out_date', 
                    'booking_status', 'payment_status', 'total_amount', 'created_at']
    list_filter = ['booking_status', 'payment_status', 'check_in_date', 'check_out_date', 'created_at']
    search_fields = ['booking_reference', 'guest__username', 'guest__email', 'listing__title', 'guest__phone_number']
    ordering = ['-created_at']
    list_editable = ['booking_status', 'payment_status']
    
    inlines = [GuestInfoInline]
    
    fieldsets = (
        ('Booking Details', {
            'fields': ('booking_reference', 'guest', 'listing')
        }),
        ('Stay Information', {
            'fields': ('check_in_date', 'check_out_date', 'number_of_guests', 'number_of_children', 'special_requests')
        }),
        ('Pricing', {
            'fields': ('nightly_price', 'total_nights', 'subtotal', 'cleaning_fee', 'service_fee', 'tax_amount', 'total_amount')
        }),
        ('Status', {
            'fields': ('booking_status', 'payment_status')
        }),
        ('Cancellation', {
            'fields': ('cancellation_reason', 'cancelled_at', 'cancelled_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['booking_reference', 'created_at', 'updated_at']
    
    date_hierarchy = 'created_at'
    
    actions = ['confirm_bookings', 'cancel_bookings', 'mark_as_completed']
    
    def confirm_bookings(self, request, queryset):
        queryset.update(booking_status='CONFIRMED')
    confirm_bookings.short_description = 'Mark selected bookings as confirmed'
    
    def cancel_bookings(self, request, queryset):
        queryset.update(booking_status='CANCELLED')
    cancel_bookings.short_description = 'Cancel selected bookings'
    
    def mark_as_completed(self, request, queryset):
        queryset.update(booking_status='COMPLETED')
    mark_as_completed.short_description = 'Mark selected bookings as completed'


@admin.register(BookingHistory)
class BookingHistoryAdmin(admin.ModelAdmin):
    """Booking History Admin"""
    list_display = ['booking', 'changed_by', 'action', 'field_name', 'changed_at']
    list_filter = ['action', 'changed_at']
    search_fields = ['booking__booking_reference', 'changed_by__username']
    readonly_fields = ['booking', 'changed_by', 'changed_at', 'field_name', 'old_value', 'new_value', 'action']
    
    date_hierarchy = 'changed_at'


@admin.register(GuestInfo)
class GuestInfoAdmin(admin.ModelAdmin):
    """Guest Info Admin"""
    list_display = ['booking', 'full_name', 'email', 'phone', 'id_type']
    search_fields = ['full_name', 'email', 'phone', 'booking__booking_reference']
    list_filter = ['id_type']
