from django.urls import path
from .views import (
    PropertyListView, PropertyDetailView, PropertyAvailabilityView,
    MyPropertiesView, PropertyCreateView, PropertyUpdateView, PropertyDeleteView,
    PropertyImageUploadView, PropertyImageDeleteView, BulkAvailabilityUpdateView,
    ApprovePropertyView, RejectPropertyView, BlockPropertyView
)

urlpatterns = [
    # Public endpoints
    path('', PropertyListView.as_view(), name='property_list'),
    path('<int:pk>/', PropertyDetailView.as_view(), name='property_detail'),
    path('<int:pk>/availability/', PropertyAvailabilityView.as_view(), name='property_availability'),
    
    # Host endpoints
    path('host/properties/', MyPropertiesView.as_view(), name='my_properties'),
    path('host/create/', PropertyCreateView.as_view(), name='property_create'),
    path('host/<int:pk>/update/', PropertyUpdateView.as_view(), name='property_update'),
    path('host/<int:pk>/delete/', PropertyDeleteView.as_view(), name='property_delete'),
    path('host/<int:pk>/images/', PropertyImageUploadView.as_view(), name='property_image_upload'),
    path('host/<int:pk>/images/<int:image_id>/', PropertyImageDeleteView.as_view(), name='property_image_delete'),
    path('host/<int:pk>/availability/bulk/', BulkAvailabilityUpdateView.as_view(), name='bulk_availability_update'),
    
    # Admin endpoints
    path('admin/<int:pk>/approve/', ApprovePropertyView.as_view(), name='approve_property'),
    path('admin/<int:pk>/reject/', RejectPropertyView.as_view(), name='reject_property'),
    path('admin/<int:pk>/block/', BlockPropertyView.as_view(), name='block_property'),
]
