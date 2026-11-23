from rest_framework.permissions import BasePermission


class IsModerator(BasePermission):
    """Проверяет, состоит ли пользователь в группе модераторов."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name="Модераторы").exists()
        )


class IsOwner(BasePermission):
    """Разрешает доступ к объекту только его владельцу."""

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class IsModeratorOrOwner(BasePermission):
    """Разрешает доступ модератору или владельцу объекта."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        is_moderator = request.user.groups.filter(
            name="Модераторы"
        ).exists()

        return is_moderator or obj.owner == request.user
