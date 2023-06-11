from rest_framework.permissions import BasePermission, IsAdminUser


class IsTokenOwner(BasePermission):
    def has_permission(self, request, view):
        pk = view.kwargs.get("pk")

        # Authenticated user id comparing to view PK
        if request.user.id == pk:
            return True
        return False


class IsTokenOwnerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return IsTokenOwner().has_permission(
            request, view
        ) or IsAdminUser().has_permission(request, view)
