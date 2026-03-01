"""Seed script for initial data: TariffPlan, SkillCatalog, SkillPreset, ToolCatalog."""

from sqlalchemy import select

from app.core.constants import SkillAccessLevel
from app.db.engine import async_session_factory
from app.models.skill import SkillCatalog, SkillPreset, skill_preset_skills
from app.models.tariff import TariffPlan
from app.models.tool import ToolCatalog

TARIFF_SEED_DATA = [
    {
        "slug": "basic",
        "name": "Базовый",
        "price_rub": 449000,
        "max_channels": 1,
        "llm_model": "qwen3-4b",
        "skills_access": SkillAccessLevel.BASIC,
        "is_self_service": True,
    },
    {
        "slug": "assistant",
        "name": "Ассистент",
        "price_rub": 999000,
        "max_channels": 3,
        "llm_model": "chatgpt-plus",
        "skills_access": SkillAccessLevel.ALL,
        "is_self_service": True,
    },
    {
        "slug": "custom",
        "name": "Кастом",
        "price_rub": 3000000,
        "max_channels": None,
        "llm_model": None,
        "skills_access": SkillAccessLevel.ALL,
        "is_self_service": False,
    },
]

SKILL_SEED_DATA = [
    {
        "slug": "schedule",
        "name": "Управление расписанием",
        "description": "Запись клиентов, управление слотами, напоминания о записях",
        "access_level": SkillAccessLevel.BASIC,
    },
    {
        "slug": "faq",
        "name": "Ответы на вопросы",
        "description": "Автоматические ответы на частые вопросы клиентов",
        "access_level": SkillAccessLevel.BASIC,
    },
    {
        "slug": "catalog",
        "name": "Каталог товаров/услуг",
        "description": "Отправка прайс-листов, описание услуг, подбор товаров",
        "access_level": SkillAccessLevel.BASIC,
    },
    {
        "slug": "orders",
        "name": "Приём заказов",
        "description": "Оформление заказов, подтверждения, отслеживание статусов",
        "access_level": SkillAccessLevel.ALL,
    },
    {
        "slug": "crm",
        "name": "CRM-интеграция",
        "description": "Сохранение контактов, история взаимодействий, теги клиентов",
        "access_level": SkillAccessLevel.ALL,
    },
    {
        "slug": "payments",
        "name": "Приём платежей",
        "description": "Генерация ссылок на оплату, подтверждение платежей",
        "access_level": SkillAccessLevel.ALL,
    },
    {
        "slug": "analytics",
        "name": "Аналитика",
        "description": "Статистика по диалогам, конверсии, популярные запросы",
        "access_level": SkillAccessLevel.ALL,
    },
    {
        "slug": "broadcast",
        "name": "Рассылки",
        "description": "Массовые и сегментированные рассылки по базе клиентов",
        "access_level": SkillAccessLevel.ALL,
    },
]

TOOL_SEED_DATA = [
    {
        "slug": "calendar",
        "name": "Google Calendar",
        "description": "Синхронизация расписания с Google Calendar",
        "config_schema": {"type": "object", "properties": {"calendar_id": {"type": "string"}}},
    },
    {
        "slug": "sheets",
        "name": "Google Sheets",
        "description": "Запись данных в таблицы Google Sheets",
        "config_schema": {"type": "object", "properties": {"spreadsheet_id": {"type": "string"}}},
    },
    {
        "slug": "webhook",
        "name": "Webhook",
        "description": "Отправка событий на произвольный URL",
        "config_schema": {"type": "object", "properties": {"url": {"type": "string"}, "secret": {"type": "string"}}},
    },
]

PRESET_SEED_DATA = [
    {
        "slug": "beauty",
        "name": "Салон красоты",
        "description": "Набор навыков для салонов красоты и бьюти-сервисов",
        "skills": ["schedule", "faq", "catalog"],
    },
    {
        "slug": "education",
        "name": "Образование",
        "description": "Набор навыков для онлайн-школ и образовательных проектов",
        "skills": ["schedule", "faq", "catalog", "payments"],
    },
    {
        "slug": "e-com",
        "name": "Интернет-магазин",
        "description": "Набор навыков для e-commerce",
        "skills": ["catalog", "orders", "payments", "faq"],
    },
    {
        "slug": "universal",
        "name": "Универсальный",
        "description": "Базовый набор навыков для любого бизнеса",
        "skills": ["schedule", "faq", "catalog"],
    },
]


async def seed_tariffs() -> None:
    async with async_session_factory() as session:
        for data in TARIFF_SEED_DATA:
            existing = await session.execute(
                select(TariffPlan).where(TariffPlan.slug == data["slug"]),
            )
            if existing.scalar_one_or_none() is None:
                session.add(TariffPlan(**data))
        await session.commit()


async def seed_skills() -> None:
    async with async_session_factory() as session:
        for data in SKILL_SEED_DATA:
            existing = await session.execute(
                select(SkillCatalog).where(SkillCatalog.slug == data["slug"]),
            )
            if existing.scalar_one_or_none() is None:
                session.add(SkillCatalog(**data))
        await session.commit()


async def seed_tools() -> None:
    async with async_session_factory() as session:
        for data in TOOL_SEED_DATA:
            existing = await session.execute(
                select(ToolCatalog).where(ToolCatalog.slug == data["slug"]),
            )
            if existing.scalar_one_or_none() is None:
                session.add(ToolCatalog(**data))
        await session.commit()


async def seed_presets() -> None:
    async with async_session_factory() as session:
        for data in PRESET_SEED_DATA:
            existing = await session.execute(
                select(SkillPreset).where(SkillPreset.slug == data["slug"]),
            )
            if existing.scalar_one_or_none() is not None:
                continue

            preset = SkillPreset(
                slug=data["slug"],
                name=data["name"],
                description=data["description"],
            )
            session.add(preset)
            await session.flush()

            for skill_slug in data["skills"]:
                skill_result = await session.execute(
                    select(SkillCatalog).where(SkillCatalog.slug == skill_slug),
                )
                skill = skill_result.scalar_one_or_none()
                if skill:
                    await session.execute(
                        skill_preset_skills.insert().values(
                            preset_id=preset.id, skill_id=skill.id,
                        ),
                    )
        await session.commit()


async def seed_all() -> None:
    await seed_tariffs()
    await seed_skills()
    await seed_tools()
    await seed_presets()


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_all())
