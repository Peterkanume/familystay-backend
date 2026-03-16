from django.contrib import admin
from .models import Review, HostReview, ReviewReport


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Review Admin"""
    list_display = ['id', 'guest', 'property', 'host', 'overall_rating', 'is_approved', 'is_reported', 'created_at']
    list_filter = ['is_approved', 'is_reported', 'overall_rating', 'created_at']
    search_fields = ['guest__username', 'property__title', 'host__username', 'comment']
    ordering = ['-created_at']
    list_editable = ['is_approved']
    
    fieldsets = (
        ('Review Details', {
            'fields': ('booking', 'guest', 'property', 'host')
        }),
        ('Ratings', {
            'fields': ('overall_rating', 'cleanliness_rating', 'communication_rating', 'checkin_rating', 
                      'accuracy_rating', 'location_rating', 'value_rating', 'child_friendly_rating', 'safety_rating')
        }),
        ('Content', {
            'fields': ('comment', 'host_reply', 'host_replied_at', 'images')
        }),
        ('Status', {
            'fields': ('is_approved', 'is_reported', 'report_reason')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'host_replied_at']
    
    date_hierarchy = 'created_at'
    
    actions = ['approve_reviews', 'disapprove_reviews', 'clear_reports']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True, is_reported=False)
    approve_reviews.short_description = 'Approve selected reviews'
    
    def disapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_reviews.short_description = 'Disapprove selected reviews'
    
    def clear_reports(self, request, queryset):
        queryset.update(is_reported=False)
    clear_reports.short_description = 'Clear reports from selected reviews'


@admin.register(HostReview)
class HostReviewAdmin(admin.ModelAdmin):
    """Host Review Admin"""
    list_display = ['id', 'guest', 'host', 'communication_rating', 'friendliness_rating', 'created_at']
    list_filter = ['created_at']
    search_fields = ['guest__username', 'host__username', 'comment']
    ordering = ['-created_at']


@admin.register(ReviewReport)
class ReviewReportAdmin(admin.ModelAdmin):
    """Review Report Admin"""
    list_display = ['id', 'review', 'reported_by', 'reason', 'status', 'resolved_by', 'created_at']
    list_filter = ['status', 'reason', 'created_at']
    search_fields = ['review__id', 'reported_by__username', 'description']
    ordering = ['-created_at']
    list_editable = ['status']
    
    fieldsets = (
        ('Report Details', {
            'fields': ('review', 'reported_by', 'reason', 'description')
        }),
        ('Resolution', {
            'fields': ('status', 'resolved_by', 'resolved_at')
        }),
    )
    
    readonly_fields = ['review', 'reported_by', 'reason', 'description', 'created_at']
    
    date_hierarchy = 'created_at'
    
    actions = ['resolve_reports', 'dismiss_reports']
    
    def resolve_reports(self, request, queryset):
        queryset.update(status='ACTION_TAKEN', resolved_by=request.user)
    resolve_reports.short_description = 'Mark selected reports as resolved'
    
    def dismiss_reports(self, request, queryset):
        queryset.update(status='DISMISSED', resolved_by=request.user)
    dismiss_reports.short_description = 'Dismiss selected reports'
