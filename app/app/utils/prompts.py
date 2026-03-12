"""
Шаблоны промптов и логика формирования MD-документов агента.

Поток:
1. Пользователь заполняет форму (name, location, about_self, occupation, agent_restrictions).
2. Данные могут быть введены небрежно — Claude приводит их в читаемый вид.
3. Результат: три MD-документа (user_md, agent_md, soul_md), сохраняемых в AgentProfile.
"""

from dataclasses import dataclass


@dataclass
class AgentFormData:
    name: str | None = None
    location: str | None = None
    about_self: str | None = None
    occupation: str | None = None
    agent_restrictions: str | None = None


# ── Системные промпты ─────────────────────────────────────────────────────────

USER_MD_SYSTEM = """Ты — AI-ассистент, который составляет USER.md документ для персонального AI-агента.
USER.md описывает владельца агента: кто он, где живёт, чем занимается, чтобы агент мог давать персонализированные ответы.

Правила:
- Пиши на русском языке
- Структурируй в Markdown
- Не придумывай детали, которых нет в исходных данных
- Если данных мало — пиши кратко, не заполняй пустыми фразами
- Сделай текст читаемым и структурированным, исправь очевидные опечатки и небрежный ввод
- Максимум 300 слов"""

AGENT_MD_SYSTEM = """Ты — AI-ассистент, который составляет AGENT.md документ — инструкцию для персонального AI-агента.
AGENT.md описывает операционные правила: что агент МОЖЕТ и НЕ МОЖЕТ делать.

Правила:
- Пиши на русском языке
- Структурируй в Markdown с секциями ## Что агент может делать и ## Что агент НЕ может делать
- Используй ограничения из формы как основу секции "не может"
- Добавляй разумные стандартные правила, если явных данных мало
- Исправь небрежный ввод пользователя
- Максимум 400 слов"""

SOUL_MD_SYSTEM = """Ты — AI-ассистент, который составляет SOUL.md документ — описание личности персонального AI-агента.
SOUL.md определяет тон общения, ценности и поведенческие паттерны агента.

Правила:
- Пиши на русском языке
- Структурируй в Markdown
- Вывери стиль общения на основе контекста пользователя (профессия, место жительства)
- Сделай агента полезным и конкретным, без лишнего формализма
- Максимум 300 слов"""


# ── Пользовательские промпты ──────────────────────────────────────────────────

def build_user_md_prompt(data: AgentFormData) -> str:
    parts = ["Составь USER.md на основе следующих данных о пользователе:\n"]
    if data.name:
        parts.append(f"Имя: {data.name}")
    if data.location:
        parts.append(f"Место жительства: {data.location}")
    if data.occupation:
        parts.append(f"Чем занимается: {data.occupation}")
    if data.about_self:
        parts.append(f"О себе: {data.about_self}")
    if len(parts) == 1:
        parts.append("Данные не заполнены — создай минимальный шаблон.")
    return "\n".join(parts)


def build_agent_md_prompt(data: AgentFormData) -> str:
    parts = ["Составь AGENT.md на основе следующих данных:\n"]
    if data.occupation:
        parts.append(f"Сфера деятельности пользователя: {data.occupation}")
    if data.agent_restrictions:
        parts.append(f"Ограничения, заданные пользователем: {data.agent_restrictions}")
    if data.about_self:
        parts.append(f"Контекст о пользователе: {data.about_self}")
    if len(parts) == 1:
        parts.append("Конкретных ограничений не задано — создай разумный стандартный набор правил.")
    return "\n".join(parts)


def build_soul_md_prompt(data: AgentFormData) -> str:
    parts = ["Составь SOUL.md на основе следующих данных:\n"]
    if data.name:
        parts.append(f"Имя пользователя: {data.name}")
    if data.location:
        parts.append(f"Место жительства: {data.location}")
    if data.occupation:
        parts.append(f"Профессия: {data.occupation}")
    if data.about_self:
        parts.append(f"О себе: {data.about_self}")
    if len(parts) == 1:
        parts.append("Данных мало — создай нейтральный профессиональный тон агента.")
    return "\n".join(parts)
