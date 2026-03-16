from django.contrib import admin
from .models import Payment, Payout, TransactionLog


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Payment Admin"""
    list_display = ['transaction_id', 'booking', 'payer', 'recipient', 'payment_method', 'amount', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'currency', 'created_at']
    search_fields = ['transaction_id', 'provider_reference', 'payer__username', 'payer__email', 'booking__booking_reference']
    ordering = ['-created_at']
    list_editable = ['status']
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('transaction_id', 'booking', 'payer', 'recipient')
        }),
        ('Transaction', {
            'fields': ('payment_method', 'amount', 'currency', 'status')
        }),
        ('Provider Info', {
            'fields': ('provider_reference', 'provider_response', 'description'),
            'classes': ('collapse',)
        }),
        ('Error Info', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['transaction_id', 'created_at', 'updated_at', 'completed_at']
    
    date_hierarchy = 'created_at'


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    """Payout Admin"""
    list_display = ['reference', 'host', 'amount', 'currency', 'payout_method', 'status', 'requested_at', 'processed_at']
    list_filter = ['status', 'payout_method', 'currency', 'requested_at']
    search_fields = ['reference', 'host__username', 'host__email']
    ordering = ['-requested_at']
    list_editable = ['status']
    
    fieldsets = (
        ('Payout Details', {
            'fields': ('reference', 'host', 'amount', 'currency', 'payout_method')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Account Details', {
            'fields': ('account_details',),
            'classes': ('collapse',)
        }),
        ('Bookings', {
            'fields': ('bookings',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['reference', 'requested_at']
    
    date_hierarchy = 'requested_at'
    
    actions = ['process_payouts', 'complete_payouts']
    
    def process_payouts(self, request, queryset):
        queryset.update(status='PROCESSING')
    process_payouts.short_description = 'Mark selected payouts as processing'
    
    def complete_payouts(self, request, queryset):
        queryset.update(status='COMPLETED')
    complete_payouts.short_description = 'Mark selected payouts as completed'


@admin.register(TransactionLog)
class TransactionLogAdmin(admin.ModelAdmin):
    """Transaction Log Admin"""
    list_display = ['transaction_type', 'transaction_id', 'user', 'amount', 'status', 'created_at']
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = ['transaction_id', 'user__username']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Transaction', {
            'fields': ('transaction_type', 'transaction_id', 'user', 'amount', 'status')
        }),
        ('Request/Response', {
            'fields': ('request_data', 'response_data'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('ip_address', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['transaction_type', 'transaction_id', 'user', 'amount', 'status', 'request_data', 'response_data', 'ip_address', 'created_at']
    
    date_hierarchy = 'created_at'
