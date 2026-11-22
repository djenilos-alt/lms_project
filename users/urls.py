from django.urls import path
from .views import UserRetrieveUpdateAPIView, PaymentListAPIView

urlpatterns = [
    path("<int:pk>/", UserRetrieveUpdateAPIView.as_view(), name="user-detail"),
    path("payments/", PaymentListAPIView.as_view(), name="payment-list"),
]