from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.mixins import AccessMixin

def role_required(allowed_roles):
    """
    Decorator to restrict view access to users with specified SkyShield roles.
    Superusers automatically pass this check.
    """
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, "Access Denied: You do not have the required role privileges to access this resource.")
            raise PermissionDenied("You do not have the required permissions for this action.")
        return _wrapped_view
    return decorator

def safety_manager_required(view_func):
    return role_required(['SAFETY_MANAGER', 'ADMINISTRATOR'])(view_func)

def investigator_required(view_func):
    return role_required(['INVESTIGATOR', 'SAFETY_MANAGER', 'ADMINISTRATOR'])(view_func)

def admin_required(view_func):
    return role_required(['ADMINISTRATOR'])(view_func)

class RoleRequiredMixin(AccessMixin):
    """CBV Mixin to enforce role requirements."""
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        if self.allowed_roles and request.user.role not in self.allowed_roles:
            messages.error(request, "Access Denied: Your account role does not have authorization for this view.")
            raise PermissionDenied("Insufficient role privileges.")
        return super().dispatch(request, *args, **kwargs)
