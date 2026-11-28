from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from .models import Course, Subscription


@shared_task
def send_course_update_email(course_id):
    """Отправляет уведомление подписчикам об обновлении курса."""

    course = Course.objects.filter(pk=course_id).first()

    if course is None:
        return "Курс не найден."

    emails = list(
        Subscription.objects.filter(
            course=course,
            user__is_active=True,
        )
        .exclude(user__email="")
        .values_list("user__email", flat=True)
        .distinct()
    )

    if not emails:
        return "У курса нет подписчиков с email."

    send_mail(
        subject=f"Обновление курса: {course.name}",
        message=(
            f"Здравствуйте!\n\n"
            f"В курсе «{course.name}» появились обновления.\n"
            f"Зайдите в личный кабинет, чтобы ознакомиться с материалами."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=emails,
        fail_silently=False,
    )

    return f"Уведомление отправлено: {len(emails)} подписчиков."
