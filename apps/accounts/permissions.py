from rest_framework import permissions


class IsGuest(permissions.BasePermission):
    """Check if user is a guest"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'GUEST'


class IsHost(permissions.BasePermission):
    """Check if user is a host"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'HOST'


class IsAdmin(permissions.BasePermission):
    """Check if user is an admin"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (request.user.role == 'ADMIN' or request.user.is_superuser)


class IsOwner(permissions.BasePermission):
    """Check if user owns the object"""
    
    def has_object_permission(self, request, view, obj):
        # Check if the object has an owner/user field
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'guest'):
            return obj.guest == request.user
        elif hasattr(obj, 'host'):
            return obj.host == request.user
        elif hasattr(obj, 'payer'):
            return obj.payer == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'sender'):
            return obj.sender == request.user
        
        return False


class IsHostOrReadOnly(permissions.BasePermission):
    """Allow hosts to edit their own properties, others can only read"""
    
    def has_object_permission(self, request, view, obj):
        # Allow read for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Allow edit only for the host
        if hasattr(obj, 'host'):
            return obj.host == request.user and request.user.role == 'HOST'
        
        return False


class CanManageProperty(permissions.BasePermission):
    """Check if user can manage a property (host and owner)"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Admins can manage all
        if request.user.role == 'ADMIN' or request.user.is_superuser:
            return True
        
        # Hosts can manage their own
        if hasattr(obj, 'host'):
            return obj.host == request.user and request.user.role == 'HOST'
        
        return False


class CanManageBooking(permissions.BasePermission):
    """Check if user can manage a booking (guest who made it or host of property)"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Admins can manage all
        if request.user.role == 'ADMIN' or request.user.is_superuser:
            return True
        
        # Guest who made the booking
        if obj.guest == request.user:
            return True
        
        # Host of the property
        if hasattr(obj, 'listing') and obj.listing.host == request.user:
            return True
        
        return False


class CanAccessConversation(permissions.BasePermission):
    """Check if user is a participant in the conversation"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        return request.user in obj.participants.all()


class CanRateBooking(permissions.BasePermission):
    """Check if user can rate a booking (only the guest who made it)"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Only the guest can rate
        if hasattr(obj, 'guest'):
            return obj.guest == request.user
        
        return False
