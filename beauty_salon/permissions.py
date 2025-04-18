# beauty_salon/permissions.py
from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Для администратора разрешаем всегда
        if request.user and request.user.is_staff:
            return True
            
        # Для обычного пользователя проверяем владение записью
        return obj.client.user == request.user