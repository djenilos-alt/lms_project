import stripe

from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework import generics, filters, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from materials.models import Course

from .models import User, Payment
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    PaymentSerializer,
    PaymentCreateSerializer,
    PaymentCreateResponseSerializer,
    PaymentStatusResponseSerializer,
    PaymentSuccessResponseSerializer,
    PaymentCancelResponseSerializer,
)
from .services import create_stripe_checkout

class UserListAPIView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class UserCreateAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]


class UserRetrieveUpdateDestroyAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]


class PaymentListAPIView(generics.ListAPIView):
    queryset = Payment.objects.none()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Payment.objects.none()

        return Payment.objects.filter(user=self.request.user)

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]

    filterset_fields = [
        "paid_course",
        "paid_lesson",
        "payment_method",
    ]

    ordering_fields = ["payment_date"]
    ordering = ["-payment_date"]
class PaymentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Создание Stripe-платежа",
        description=(
            "Создаёт платёж за курс и Stripe Checkout Session. "
            "Стоимость берётся из цены курса."
        ),
        request=PaymentCreateSerializer,
        responses={
            201: PaymentCreateResponseSerializer,
            400: None,
            502: None,
        },
    )
    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        course_id = serializer.validated_data["course_id"]
        course = get_object_or_404(Course, pk=course_id)

        if course.price <= 0:
            return Response(
                {"error": "Стоимость курса должна быть больше нуля."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = Payment.objects.create(
            user=request.user,
            paid_course=course,
            amount=course.price,
            payment_method="stripe",
            status="pending",
        )

        try:
            session = create_stripe_checkout(
                payment=payment,
                success_url=settings.STRIPE_SUCCESS_URL,
                cancel_url=settings.STRIPE_CANCEL_URL,
            )
        except stripe.StripeError:
            payment.status = "failed"
            payment.save(update_fields=["status"])

            return Response(
                {"error": "Не удалось создать платёж в Stripe."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except ValueError as exc:
            payment.status = "failed"
            payment.save(update_fields=["status"])

            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "payment_id": payment.id,
                "status": payment.status,
                "payment_url": session.url,
                "stripe_session_id": session.id,
            },
            status=status.HTTP_201_CREATED,
        )

class PaymentStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Проверка статуса Stripe-платежа",
        description=(
            "Получает актуальный статус Checkout Session из Stripe "
            "и обновляет статус платежа в базе данных."
        ),
        responses={
            200: PaymentStatusResponseSerializer,
            400: None,
            502: None,
        },
    )
    def get(self, request, pk):
        payment = get_object_or_404(
            Payment,
            pk=pk,
            user=request.user,
        )

        if not payment.stripe_session_id:
            return Response(
                {"error": "Для платежа не создана Stripe-сессия."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            session = stripe.checkout.Session.retrieve(
                payment.stripe_session_id
            )
        except stripe.StripeError:
            return Response(
                {"error": "Не удалось получить статус платежа из Stripe."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if session.payment_status == "paid":
            payment.status = "paid"
        elif session.status == "expired":
            payment.status = "expired"

        payment.save(update_fields=["status"])

        return Response(
            {
                "payment_id": payment.id,
                "status": payment.status,
                "stripe_session_status": session.status,
                "stripe_payment_status": session.payment_status,
            },
            status=status.HTTP_200_OK,
        )

class PaymentSuccessAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Возврат после успешной оплаты",
        description="Проверяет Stripe Checkout Session и обновляет платёж.",
        responses={
            200: PaymentSuccessResponseSerializer,
            400: None,
            404: None,
            502: None,
        },
    )
    def get(self, request):
        session_id = request.query_params.get("session_id")

        if not session_id:
            return Response(
                {"error": "Не указан session_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except stripe.StripeError:
            return Response(
                {"error": "Не удалось проверить платёж в Stripe."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payment = Payment.objects.filter(
            stripe_session_id=session.id
        ).first()

        if not payment:
            return Response(
                {"error": "Платёж не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if session.payment_status == "paid":
            payment.status = "paid"
            payment.save(update_fields=["status"])

        return Response(
            {
                "message": "Оплата успешно проверена.",
                "payment_id": payment.id,
                "status": payment.status,
                "stripe_session_status": session.status,
                "stripe_payment_status": session.payment_status,
            },
            status=status.HTTP_200_OK,
        )


class PaymentCancelAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Возврат после отмены оплаты",
        description="Сообщает пользователю об отмене оплаты.",
        responses={
            200: PaymentCancelResponseSerializer,
        },
    )
    def get(self, request):
        return Response(
            {
                "message": "Оплата отменена пользователем.",
                "status": "pending",
            },
            status=status.HTTP_200_OK,
        )
