from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.utils import timezone
from datetime import timedelta
from .tokens import CustomToken


class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication that tracks user activity and enforces session timeout.
    """

    def authenticate(self, request):
        """
        Authenticate the request and return a tuple of (user, token).
        """
        result = super().authenticate(request)
        
        if result is None:
            return None

        user, validated_token = result
        
        # Check if token is blacklisted (for rotated tokens)
        if hasattr(validated_token, 'blacklist'):
            if validated_token in validated_token.blacklist.all():
                raise AuthenticationFailed('Token has been invalidated')

        # Check custom token activity
        token_key = validated_token.payload.get('jti', None)
        if token_key:
            try:
                custom_token = CustomToken.objects.get(
                    key=token_key,
                    user=user,
                    is_active=True
                )
                
                # Check if token has expired due to inactivity
                if custom_token.is_expired:
                    # Invalidate the token
                    custom_token.is_active = False
                    custom_token.save(update_fields=['is_active'])
                    raise AuthenticationFailed('Session expired due to inactivity. Please log in again.')
                
                # Update last activity
                custom_token.update_activity()
                
            except CustomToken.DoesNotExist:
                # Token not found in custom tokens - allow standard JWT validation
                pass
            except Exception as e:
                # Log error but don't block authentication
                pass

        return (user, validated_token)


class SessionTimeoutMiddleware:
    """
    Middleware to check for session timeout on each request.
    This provides an additional layer of security.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for unauthenticated requests
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Check for token activity
        token_key = request.auth
        if token_key:
            try:
                # Try to find custom token
                custom_token = CustomToken.objects.filter(
                    user=request.user,
                    is_active=True
                ).first()
                
                if custom_token and custom_token.is_expired:
                    # Token expired due to inactivity
                    custom_token.is_active = False
                    custom_token.save(update_fields=['is_active'])
                    
                    # Return 401 Unauthorized
                    from rest_framework.response import Response
                    from rest_framework import status
                    return Response(
                        {'detail': 'Session expired due to inactivity. Please log in again.'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                    
            except Exception:
                pass

        response = self.get_response(request)
        return response
