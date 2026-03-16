from django.contrib import admin
from .models import Property, PropertyImage, Availability


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ['image', 'is_featured', 'caption', 'uploaded_at']
    readonly_fields = ['uploaded_at']


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """Property Admin"""
    list_display = ['title', 'host', 'city', 'country', 'property_type', 'status', 'is_available', 'base_price', 'created_at']
    list_filter = ['status', 'is_available', 'property_type', 'city', 'country', 'bedrooms', 'created_at']
    search_fields = ['title', 'description', 'host__username', 'host__email', 'address', 'city']
    ordering = ['-created_at']
    list_editable = ['status', 'is_available']
    
    inlines = [PropertyImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('host', 'title', 'description', 'property_type')
        }),
        ('Location', {
            'fields': ('address', 'city', 'state', 'country', 'zip_code', 'latitude', 'longitude')
        }),
        ('Property Details', {
            'fields': ('bedrooms', 'bathrooms', 'max_guests', 'square_feet')
        }),
        ('Amenities & Features', {
            'fields': ('amenities', 'family_features'),
            'classes': ('collapse',)
        }),
        ('Pricing', {
            'fields': ('base_price', 'cleaning_fee', 'service_fee', 'security_deposit')
        }),
        ('Media', {
            'fields': ('featured_image',)
        }),
        ('Status', {
            'fields': ('status', 'is_available', 'views_count')
        }),
    )
    
    readonly_fields = ['views_count', 'created_at', 'updated_at']
    
    actions = ['approve_properties', 'reject_properties', 'block_properties']
    
    def approve_properties(self, request, queryset):
        queryset.update(status='APPROVED')
    approve_properties.short_description = 'Approve selected properties'
    
    def reject_properties(self, request, queryset):
        queryset.update(status='REJECTED')
    reject_properties.short_description = 'Reject selected properties'
    
    def block_properties(self, request, queryset):
        queryset.update(status='BLOCKED', is_available=False)
    block_properties.short_description = 'Block selected properties'


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ['property', 'is_featured', 'caption', 'uploaded_at']
    list_filter = ['is_featured', 'uploaded_at']
    search_fields = ['property__title', 'caption']


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ['property', 'date', 'is_available', 'price_override']
    list_filter = ['is_available', 'date']
    search_fields = ['property__title']
    date_hierarchy = 'date'
