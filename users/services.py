import stripe
from django.conf import settings


def create_stripe_checkout(payment, success_url, cancel_url):
    """Создаёт продукт, цену и Checkout Session в Stripe."""

    if not payment.paid_course:
        raise ValueError("Для Stripe-оплаты необходимо указать курс.")

    if payment.amount <= 0:
        raise ValueError("Стоимость курса должна быть больше нуля.")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    course = payment.paid_course

    # Создаём продукт Stripe.
    product = stripe.Product.create(
        name=course.name,
        description=course.description or None,
    )

    # Создаём цену. Stripe принимает сумму в копейках.
    price = stripe.Price.create(
        product=product.id,
        unit_amount=int(payment.amount * 100),
        currency="rub",
    )

    # Создаём сессию оплаты.
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price": price.id,
                "quantity": 1,
            }
        ],
        customer_email=payment.user.email,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "payment_id": str(payment.id),
        },
    )

    # Сохраняем данные Stripe в нашей базе.
    payment.stripe_product_id = product.id
    payment.stripe_price_id = price.id
    payment.stripe_session_id = session.id
    payment.payment_url = session.url
    payment.save(
        update_fields=[
            "stripe_product_id",
            "stripe_price_id",
            "stripe_session_id",
            "payment_url",
        ]
    )

    return session
