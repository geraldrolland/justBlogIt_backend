from rest_framework.permissions import BasePermission

class IsStaffPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_staff == True:
            return True
        return False
    
class IsAdminPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser == True:
            return True
        return False
    