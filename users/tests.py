from types import SimpleNamespace
from unittest.mock import patch

import stripe

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from materials.models import Course
from users.models import User, Payment


class StripePaymentTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="student@example.com",
            password="testpassword123",
            first_name="Тест",
            last_name="Студент",
        )

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpassword123",
            first_name="Другой",
            last_name="Пользователь",
        )

        self.course = Course.objects.create(
            name="Тестовый курс",
            description="Описание курса",
            price=4500,
            owner=self.user,
        )

        self.client.force_authenticate(user=self.user)

    def test_create_payment_success(self):
        with patch(
            "users.services.stripe.Product.create"
        ) as mock_product, patch(
            "users.services.stripe.Price.create"
        ) as mock_price, patch(
            "users.services.stripe.checkout.Session.create"
        ) as mock_session:

            mock_product.return_value = SimpleNamespace(
                id="prod_test_123"
            )

            mock_price.return_value = SimpleNamespace(
                id="price_test_123"
            )

            mock_session.return_value = SimpleNamespace(
                id="cs_test_123",
                url="https://checkout.stripe.com/test",
            )

            response = self.client.post(
                "/api/users/payments/create/",
                {"course_id": self.course.id},
                format="json",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        payment = Payment.objects.get(user=self.user)

        self.assertEqual(payment.amount, self.course.price)
        self.assertEqual(payment.status, "pending")
        self.assertEqual(payment.payment_method, "stripe")

        self.assertEqual(
            payment.stripe_product_id,
            "prod_test_123",
        )
        self.assertEqual(
            payment.stripe_price_id,
            "price_test_123",
        )
        self.assertEqual(
            payment.stripe_session_id,
            "cs_test_123",
        )
        self.assertEqual(
            payment.payment_url,
            "https://checkout.stripe.com/test",
        )


    @patch("users.views.create_stripe_checkout")
    def test_create_payment_stripe_error(self, mock_checkout):
        mock_checkout.side_effect = stripe.StripeError(
            "Stripe unavailable"
        )

        response = self.client.post(
            "/api/users/payments/create/",
            {"course_id": self.course.id},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_502_BAD_GATEWAY,
        )

        payment = Payment.objects.get(user=self.user)
        self.assertEqual(payment.status, "failed")

    def test_create_payment_with_zero_price(self):
        self.course.price = 0
        self.course.save(update_fields=["price"])

        response = self.client.post(
            "/api/users/payments/create/",
            {"course_id": self.course.id},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            Payment.objects.filter(user=self.user).exists()
        )

    @patch("users.views.stripe.checkout.Session.retrieve")
    def test_payment_status_paid(self, mock_retrieve):
        payment = Payment.objects.create(
            user=self.user,
            paid_course=self.course,
            amount=4500,
            payment_method="stripe",
            stripe_session_id="cs_test_paid",
        )

        mock_retrieve.return_value = SimpleNamespace(
            id="cs_test_paid",
            status="complete",
            payment_status="paid",
        )

        response = self.client.get(
            f"/api/users/payments/{payment.id}/status/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payment.refresh_from_db()
        self.assertEqual(payment.status, "paid")

        self.assertEqual(
            response.data["stripe_session_status"],
            "complete",
        )
        self.assertEqual(
            response.data["stripe_payment_status"],
            "paid",
        )

    def test_cannot_check_another_users_payment(self):
        payment = Payment.objects.create(
            user=self.other_user,
            paid_course=self.course,
            amount=4500,
            payment_method="stripe",
            stripe_session_id="cs_test_other",
        )

        response = self.client.get(
            f"/api/users/payments/{payment.id}/status/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
