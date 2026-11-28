from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .validators import validate_youtube_url

from .models import Course, Lesson, Subscription


class LessonSerializer(serializers.ModelSerializer):
    video_url = serializers.URLField(
        required=False,
        allow_blank=True,
        validators=[validate_youtube_url],
    )

    class Meta:
        model = Lesson
        fields = "__all__"
        read_only_fields = ("owner",)

class SubscriptionRequestSerializer(serializers.Serializer):
    course_id = serializers.IntegerField(
        help_text="ID курса, на который нужно подписаться или отписаться."
    )

class SubscriptionResponseSerializer(serializers.Serializer):
    message = serializers.CharField(
        help_text="Результат операции с подпиской."
    )


class CourseSerializer(serializers.ModelSerializer):
    lesson_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            "id",
            "name",
            "preview",
            "description",
            "price",
            "lesson_count",
            "lessons",
            "is_subscribed",
        )

    @extend_schema_field(serializers.IntegerField())
    def get_lesson_count(self, obj):
        return obj.lessons.count()

    @extend_schema_field(serializers.BooleanField())
    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        if not user.is_authenticated:
            return False

        return Subscription.objects.filter(
            user=user,
            course=obj,
        ).exists()
