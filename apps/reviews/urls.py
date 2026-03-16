from django.urls import path
from .views import (
    CreateReviewView, PropertyReviewsView, UpdateReviewView,
    DeleteReviewView, HostReplyView, ReportReviewView,
    ModerateReviewView
)

urlpatterns = [
    # Review endpoints
    path('create/', CreateReviewView.as_view(), name='create_review'),
    path('property/<int:property_id>/', PropertyReviewsView.as_view(), name='property_reviews'),
    path('<int:pk>/', UpdateReviewView.as_view(), name='update_review'),
    path('<int:pk>/delete/', DeleteReviewView.as_view(), name='delete_review'),
    path('<int:review_id>/reply/', HostReplyView.as_view(), name='host_reply'),
    path('<int:review_id>/report/', ReportReviewView.as_view(), name='report_review'),
    
    # Admin endpoints
    path('admin/<int:review_id>/moderate/', ModerateReviewView.as_view(), name='moderate_review'),
]
