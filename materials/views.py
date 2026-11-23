from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import Course, Lesson
from .serializers import CourseSerializer, LessonSerializer
from .permissions import IsModerator, IsOwner, IsModeratorOrOwner


class CourseViewSet(ModelViewSet):
    serializer_class = CourseSerializer

    def get_queryset(self):
        user = self.request.user

        if IsModerator().has_permission(self.request, self):
            return Course.objects.all()

        return Course.objects.filter(owner=user)

    def get_permissions(self):
        if self.action in ["list", "create"]:
            return [IsAuthenticated()]

        if self.action in ["retrieve", "update", "partial_update"]:
            return [IsAuthenticated(), IsModeratorOrOwner()]

        if self.action == "destroy":
            return [IsAuthenticated(), IsOwner()]

        return super().get_permissions()

    def perform_create(self, serializer):
        if IsModerator().has_permission(self.request, self):
            raise PermissionDenied(
                "Модератор не может создавать курсы."
            )

        serializer.save(owner=self.request.user)


class LessonListCreateAPIView(ListCreateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if IsModerator().has_permission(self.request, self):
            return Lesson.objects.all()

        return Lesson.objects.filter(owner=user)

    def perform_create(self, serializer):
        if IsModerator().has_permission(self.request, self):
            raise PermissionDenied(
                "Модератор не может создавать уроки."
            )

        serializer.save(owner=self.request.user)


class LessonRetrieveUpdateDestroyAPIView(
    RetrieveUpdateDestroyAPIView
):
    serializer_class = LessonSerializer

    def get_queryset(self):
        user = self.request.user

        if IsModerator().has_permission(self.request, self):
            return Lesson.objects.all()

        return Lesson.objects.filter(owner=user)

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsOwner()]

        return [IsAuthenticated(), IsModeratorOrOwner()]
