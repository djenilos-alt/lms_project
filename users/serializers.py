from rest_framework import serializers

from .models import User, Payment
from django.contrib.auth.password_validation import validate_password


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone",
            "city",
            "avatar",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(
            password=password,
            **validated_data,
        )


class UserSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "city",
            "avatar",
            "payments",
        )
        read_only_fields = ("id",)

    def to_representation(self, instance):
        data = super().to_representation(instance)

        request = self.context.get("request")

        if request and instance.pk != request.user.pk:
            data.pop("last_name", None)
            data.pop("payments", None)

        return data
class PaymentCreateSerializer(serializers.Serializer):
    course_id = serializers.IntegerField(
        help_text="ID курса, который пользователь хочет оплатить."
    )


class PaymentCreateResponseSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField()
    status = serializers.CharField()
    payment_url = serializers.URLField()
    stripe_session_id = serializers.CharField()

class PaymentStatusResponseSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField()
    status = serializers.CharField()
    stripe_session_status = serializers.CharField()
    stripe_payment_status = serializers.CharField()

class PaymentSuccessResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    payment_id = serializers.IntegerField()
    status = serializers.CharField()
    stripe_session_status = serializers.CharField()
    stripe_payment_status = serializers.CharField()


class PaymentCancelResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    status = serializers.CharField()
