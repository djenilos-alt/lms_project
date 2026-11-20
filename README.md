# LMS Project

REST API для управления учебными курсами и уроками.

## Технологии

- Python 3.13
- Django
- Django REST Framework
- Poetry
- SQLite

## Структура проекта

- config — настройки Django-проекта.
- materials — приложение курсов и уроков.
- users — приложение пользователей.

## Установка и запуск

Установить зависимости:

    poetry install

Применить миграции:

    poetry run python manage.py migrate

Запустить сервер:

    poetry run python manage.py runserver

## API

### Курсы

- GET /api/courses/ — список курсов.
- POST /api/courses/ — создание курса.
- GET /api/courses/{id}/ — просмотр курса.
- PUT /api/courses/{id}/ — полное обновление курса.
- PATCH /api/courses/{id}/ — частичное обновление курса.
- DELETE /api/courses/{id}/ — удаление курса.

### Уроки

- GET /api/lessons/ — список уроков.
- POST /api/lessons/ — создание урока.
- GET /api/lessons/{id}/ — просмотр урока.
- PUT /api/lessons/{id}/ — полное обновление урока.
- PATCH /api/lessons/{id}/ — частичное обновление урока.
- DELETE /api/lessons/{id}/ — удаление урока.

### Пользователи

- GET /api/users/{id}/ — просмотр профиля.
- PATCH /api/users/{id}/ — обновление профиля.

## Проверка

API проверялось с помощью Postman.
