from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from .serializers import (
    UserSerializer, UserRegistrationSerializer, UserLoginSerializer,
    UserProfileUpdateSerializer, PasswordChangeSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)
from .permissions import IsAdmin
from .tokens import get_tokens_for_user, CustomToken
from .authentication import CustomJWTAuthentication

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """User registration endpoint"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """User login endpoint"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            # Try email login
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'error': 'Account is disabled'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generate custom tokens with activity tracking
        tokens = get_tokens_for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens
        })


class LogoutView(APIView):
    """User logout endpoint"""
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({'message': 'Logged out successfully'})
        except Exception as e:
            return Response({'message': 'Logged out'})


class ProfileView(generics.RetrieveUpdateAPIView):
    """Get or update user profile"""
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserProfileUpdateSerializer
        return UserSerializer
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(UserSerializer(instance).data)


class PasswordChangeView(APIView):
    """Change user password"""
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Password changed successfully'})


class TokenRefreshView(APIView):
    """Refresh access token"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            
            return Response({
                'access': str(token.access_token)
            })
        except Exception as e:
            return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)


class VerifyEmailView(generics.GenericAPIView):
    """Verify user email"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, token):
        # In production, validate token and mark email as verified
        # For now, return success
        return Response({'message': 'Email verified successfully'})


class RequestPasswordResetView(APIView):
    """Request password reset"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            # In production, send password reset email
            # For now, return success
            return Response({
                'message': 'Password reset link sent to your email'
            })
        except User.DoesNotExist:
            # Don't reveal if email exists
            return Response({
                'message': 'If the email exists, a reset link will be sent'
            })


class ResetPasswordView(APIView):
    """Reset password with token"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # In production, validate token and reset password
        # For now, return success
        return Response({'message': 'Password reset successfully'})


class UserListView(generics.ListAPIView):
    """List all users (Admin only)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by role
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter by verification status
        email_verified = self.request.query_params.get('email_verified')
        if email_verified:
            queryset = queryset.filter(email_verified=email_verified.lower() == 'true')
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                username__icontains=search
            ) | queryset.filter(
                email__icontains=search
            )
        
        return queryset


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update or delete a user (Admin only)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
