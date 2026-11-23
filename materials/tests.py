from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from materials.models import Course, Lesson, Subscription

User = get_user_model()


class LessonTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Первый пользователь
        self.user = User.objects.create_user(
            email="lesson_test@example.com",
            password="testpass123",
        )

        # Его курс
        self.course = Course.objects.create(
            name="Тестовый курс",
            description="Описание тестового курса",
            owner=self.user,
        )

        # Его урок
        self.lesson = Lesson.objects.create(
            name="Тестовый урок",
            description="Описание тестового урока",
            course=self.course,
            owner=self.user,
            video_url="https://www.youtube.com/watch?v=abc123",
        )

        # Второй пользователь
        self.other_user = User.objects.create_user(
            email="other_user@example.com",
            password="testpass123",
        )

        # Курс второго пользователя
        self.other_course = Course.objects.create(
            name="Чужой курс",
            description="Описание чужого курса",
            owner=self.other_user,
        )

        # Урок второго пользователя
        self.other_lesson = Lesson.objects.create(
            name="Чужой урок",
            description="Описание чужого урока",
            course=self.other_course,
            owner=self.other_user,
            video_url="https://www.youtube.com/watch?v=other123",
        )

        self.client.force_authenticate(user=self.user)

    def test_lesson_list(self):
        response = self.client.get("/api/lessons/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["name"],
            "Тестовый урок",
        )

    def test_lesson_create(self):
        data = {
            "name": "Новый урок",
            "description": "Описание нового урока",
            "course": self.course.id,
            "video_url": "https://www.youtube.com/watch?v=xyz789",
        }

        response = self.client.post(
            "/api/lessons/",
            data=data,
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "Новый урок")
        self.assertEqual(Lesson.objects.count(), 3)

    def test_lesson_retrieve(self):
        response = self.client.get(
            f"/api/lessons/{self.lesson.id}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Тестовый урок")

    def test_lesson_update(self):
        data = {
            "name": "Обновлённый урок",
        }

        response = self.client.patch(
            f"/api/lessons/{self.lesson.id}/",
            data=data,
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Обновлённый урок")

    def test_lesson_delete(self):
        response = self.client.delete(
            f"/api/lessons/{self.lesson.id}/"
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            Lesson.objects.filter(id=self.lesson.id).exists()
        )

    def test_user_cannot_retrieve_other_lesson(self):
        response = self.client.get(
            f"/api/lessons/{self.other_lesson.id}/"
        )

        self.assertEqual(response.status_code, 404)

    def test_user_cannot_update_other_lesson(self):
        response = self.client.patch(
            f"/api/lessons/{self.other_lesson.id}/",
            data={"name": "Попытка изменить чужой урок"},
            format="json",
        )

        self.assertEqual(response.status_code, 404)

        self.other_lesson.refresh_from_db()
        self.assertEqual(self.other_lesson.name, "Чужой урок")

    def test_user_cannot_delete_other_lesson(self):
        response = self.client.delete(
            f"/api/lessons/{self.other_lesson.id}/"
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            Lesson.objects.filter(id=self.other_lesson.id).exists()
        )

    def test_subscription_create(self):
        response = self.client.post(
            "/api/subscriptions/",
            data={"course_id": self.other_course.id},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Subscription.objects.filter(
                user=self.user,
                course=self.other_course,
            ).exists()
        )

    def test_subscription_delete(self):
        # Сначала создаём подписку
        Subscription.objects.create(
            user=self.user,
            course=self.other_course,
        )

        # Повторный запрос отменяет подписку
        response = self.client.post(
            "/api/subscriptions/",
            data={"course_id": self.other_course.id},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Subscription.objects.filter(
                user=self.user,
                course=self.other_course,
            ).exists()
        )
