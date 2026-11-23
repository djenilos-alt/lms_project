
from django.urls import path

from .views import (
    UserListAPIView,
    UserCreateAPIView,
    UserRetrieveUpdateDestroyAPIView,
    PaymentListAPIView,
)

urlpatterns = [
    path("", UserListAPIView.as_view(), name="user-list"),
    path("register/", UserCreateAPIView.as_view(), name="user-register"),
    path("payments/", PaymentListAPIView.as_view(), name="payment-list"),
    path(
        "<int:pk>/",
        UserRetrieveUpdateDestroyAPIView.as_view(),
        name="user-detail",
    ),
]
