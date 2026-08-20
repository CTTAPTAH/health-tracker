from rest_framework.permissions import BasePermission

class IsOwner(BasePermission):
    """Разрешает доступ к объекту только его владельцу"""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user