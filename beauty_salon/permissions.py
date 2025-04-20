# beauty_salon/permissions.py
from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Разрешение, позволяющее только владельцу объекта или администратору его редактировать/удалять.
    """

    def has_object_permission(self, request, view, obj):
        # Разрешить GET, HEAD или OPTIONS запросы всем
        if request.method in permissions.SAFE_METHODS:
            return True

        # Для остальных методов проверяем, является ли пользователь владельцем или администратором
        if hasattr(obj, 'client'):
            return obj.client.user == request.user or request.user.is_staff
        elif hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_staff
        return request.user.is_staff


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешение, позволяющее только администраторам редактировать/удалять объекты.
    Остальные могут только просматривать.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff