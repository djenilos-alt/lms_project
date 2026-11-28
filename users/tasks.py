from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import User


@shared_task
def deactivate_inactive_users():
    """Деактивирует пользователей, не входивших более 30 дней."""

    inactive_date = timezone.now() - timedelta(days=30)

    updated_count = User.objects.filter(
        last_login__lt=inactive_date,
        is_active=True,
    ).update(is_active=False)

    return f"Деактивировано пользователей: {updated_count}"
