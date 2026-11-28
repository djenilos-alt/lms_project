from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import Course, Lesson, Subscription
from .serializers import (
    CourseSerializer,
    LessonSerializer,
    SubscriptionRequestSerializer,
    SubscriptionResponseSerializer,
)
from .permissions import IsModerator, IsOwner, IsModeratorOrOwner
from drf_spectacular.utils import extend_schema

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .paginators import MaterialsPagination


class CourseViewSet(ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    pagination_class = MaterialsPagination

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
    pagination_class = MaterialsPagination

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


class SubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Подписка на курс или отмена подписки",
        description=(
                "Если подписки ещё нет — создаёт её. "
                "Если подписка существует — удаляет её."
        ),
        request=SubscriptionRequestSerializer,
        responses={
            200: SubscriptionResponseSerializer,
            201: SubscriptionResponseSerializer,
            400: SubscriptionResponseSerializer,
            404: SubscriptionResponseSerializer,
        },
    )

    def post(self, request, *args, **kwargs):
        course_id = request.data.get("course_id")

        if not course_id:
            return Response(
                {"message": "Необходимо указать course_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response(
                {"message": "Курс не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        subscription = Subscription.objects.filter(
            user=request.user,
            course=course,
        )

        if subscription.exists():
            subscription.delete()
            return Response(
                {"message": "Подписка на курс отменена."},
                status=status.HTTP_200_OK,
            )

        Subscription.objects.create(
            user=request.user,
            course=course,
        )

        return Response(
            {"message": "Вы подписались на курс."},
            status=status.HTTP_201_CREATED,
        )