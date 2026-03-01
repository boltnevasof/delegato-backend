# Delegato Backend

Backend-часть SaaS-платформы **Delegato** — сервиса для создания, настройки и управления персональными AI-агентами, развёрнутыми на выделенных серверах клиентов.

## Что делает платформа

Пользователь проходит онбординг: описывает свой бизнес, выбирает навыки и каналы связи (Telegram). Платформа автоматически разворачивает выделенный сервер через Terraform (TimeWeb Cloud), конфигурирует его через Ansible (Docker + OpenClaw) и запускает AI-агента, готового к работе.

## Основные возможности

- **Аутентификация** — email OTP, Google OAuth, Telegram Login
- **Онбординг агента** — пошаговая настройка: описание бизнеса, SOUL.md / AGENT.md, навыки, инструменты, каналы
- **AI-генерация** — автоматическое создание и улучшение конфигурации агента через Claude API
- **Провижининг серверов** — автоматическое создание VPS (Terraform) и конфигурация (Ansible) с изоляцией состояний
- **Тарифы и подписки** — каталог тарифов, оплата через TBank / YooKassa, пропорциональный пересчёт при смене тарифа
- **Админ-панель** — управление пользователями, серверами, агентами и заявками

## Стек

- **Python 3.12+**, **FastAPI**, **SQLAlchemy 2.0** (async), **PostgreSQL**
- **Redis** + **Taskiq** (фоновые задачи)
- **Terraform** (TimeWeb Cloud) + **Ansible** (Docker + OpenClaw)
- **Alembic** (миграции), **Poetry** (зависимости), **Pydantic v2** (валидация)
- **JWT** авторизация, **slowapi** rate limiting, **Sentry** мониторинг

## Структура проекта

```
app/
  app/
    api/v1/endpoints/   # REST API эндпоинты
    api/v1/schemas/     # Pydantic-схемы запросов/ответов
    core/               # Конфигурация, константы, DI-контейнер
    db/                 # SQLAlchemy engine, базовая модель
    models/             # ORM-модели
    repositories/       # Слой доступа к данным
    services/           # Бизнес-логика
    tasks/              # Фоновые задачи (Taskiq)
    migrations/         # Alembic миграции
infrastructure/
  terraform/            # IaC для создания серверов
  ansible/              # Конфигурация серверов (Docker + OpenClaw)
```

## Быстрый старт

```bash
cd app
cp .env.example .env        # заполнить переменные окружения
poetry install               # установить зависимости
alembic upgrade head         # применить миграции
uvicorn app.main:app --reload
```

API-документация доступна по адресу `http://localhost:8000/docs` (только в DEBUG-режиме).
