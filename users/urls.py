from django.urls import path

from .views import (
    UserListAPIView,
    UserCreateAPIView,
    UserRetrieveUpdateDestroyAPIView,
    PaymentListAPIView,
    PaymentCreateAPIView,
    PaymentStatusAPIView,
    PaymentSuccessAPIView,
    PaymentCancelAPIView,
)

urlpatterns = [
    path("", UserListAPIView.as_view(), name="user-list"),
    path("register/", UserCreateAPIView.as_view(), name="user-register"),
    path("payments/", PaymentListAPIView.as_view(), name="payment-list"),
    path(
        "payments/create/",
        PaymentCreateAPIView.as_view(),
         name="payment-create",
    ),
    path(
        "payments/success/",
        PaymentSuccessAPIView.as_view(),
        name="payment-success",
    ),
    path(
        "payments/cancel/",
        PaymentCancelAPIView.as_view(),
        name="payment-cancel",
    ),
    path(
        "payments/<int:pk>/status/",
        PaymentStatusAPIView.as_view(),
        name="payment-status",
    ),
    path(
        "<int:pk>/",
        UserRetrieveUpdateDestroyAPIView.as_view(),
        name="user-detail",
    ),
]
