from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, LogoutView, ProfileView,
    PasswordChangeView, VerifyEmailView, RequestPasswordResetView,
    ResetPasswordView, UserListView, UserDetailView
)

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Profile
    path('profile/', ProfileView.as_view(), name='profile'),
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
    
    # Email verification
    path('verify-email/<str:token>/', VerifyEmailView.as_view(), name='verify_email'),
    
    # Password reset
    path('password-reset/', RequestPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/confirm/', ResetPasswordView.as_view(), name='password_reset_confirm'),
    
    # Admin endpoints
    path('admin/users/', UserListView.as_view(), name='user_list'),
    path('admin/users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
]
