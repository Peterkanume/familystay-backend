from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# API Documentation setup
schema_view = get_schema_view(
    openapi.Info(
        title="FamilyStay Booking API",
        default_version='v1',
        description="API for FamilyStay Booking System",
        contact=openapi.Contact(email="your-email@example.com"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/auth/', include('apps.accounts.urls')),
    path('api/properties/', include('apps.properties.urls')),
    path('api/bookings/', include('apps.bookings.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/reviews/', include('apps.reviews.urls')),
    path('api/communications/', include('apps.communications.urls')),
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)