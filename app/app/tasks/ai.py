import uuid

from loguru import logger

from app.broker import broker
from app.db.engine import session_context
from app.services.ai import AIService
from app.utils.prompts import (
    AGENT_MD_SYSTEM,
    SOUL_MD_SYSTEM,
    USER_MD_SYSTEM,
    AgentFormData,
    build_agent_md_prompt,
    build_soul_md_prompt,
    build_user_md_prompt,
)


@broker.task
async def generate_soul_md_task(agent_id: str, business_description: str) -> dict:
    """Generate SOUL.md and AGENT.md via Claude API, store on Agent record."""
    logger.info("Starting AI generation for agent={agent_id}", agent_id=agent_id)

    ai_service = AIService()
    result = await ai_service.generate_soul_and_agent_md(business_description)

    from app.core.container import Container
    session = Container.session()
    token = session_context.set(session)
    try:
        repo = Container.agent_repository()
        await repo.update(
            uuid.UUID(agent_id),
            soul_md=result["soul_md"],
            agent_md=result["agent_md"],
            onboarding_step=1,
        )
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
        session_context.reset(token)

    logger.info("AI generation completed for agent={agent_id}", agent_id=agent_id)
    return result


@broker.task
async def generate_about_task(
    user_id: str,
    name: str | None,
    location: str | None,
    about_self: str | None,
    occupation: str | None,
    agent_restrictions: str | None,
) -> dict:
    """
    Формирует user_md, agent_md, soul_md из данных формы через Claude API.
    Сохраняет результат в agent_documents.
    """
    logger.info("Starting about generation for user={user_id}", user_id=user_id)

    form_data = AgentFormData(
        name=name,
        location=location,
        about_self=about_self,
        occupation=occupation,
        agent_restrictions=agent_restrictions,
    )

    ai_service = AIService()
    user_md = await ai_service._call_claude(
        system=USER_MD_SYSTEM,
        user=build_user_md_prompt(form_data),
    )
    agent_md = await ai_service._call_claude(
        system=AGENT_MD_SYSTEM,
        user=build_agent_md_prompt(form_data),
    )
    soul_md = await ai_service._call_claude(
        system=SOUL_MD_SYSTEM,
        user=build_soul_md_prompt(form_data),
    )

    from app.core.container import Container
    session = Container.session()
    token = session_context.set(session)
    try:
        repo = Container.agent_document_repository()
        await repo.upsert(
            uuid.UUID(user_id),
            user_md=user_md,
            agent_md=agent_md,
            soul_md=soul_md,
        )
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
        session_context.reset(token)

    logger.info("About generation completed for user={user_id}", user_id=user_id)
    return {"user_md": user_md, "agent_md": agent_md, "soul_md": soul_md}


@broker.task
async def enhance_content_task(agent_id: str, field: str, content: str) -> dict:
    """Enhance SOUL.md or AGENT.md via Claude API."""
    logger.info(
        "Starting AI enhancement for agent={agent_id} field={field}",
        agent_id=agent_id, field=field,
    )

    ai_service = AIService()
    enhanced = await ai_service.enhance_content(field, content)

    logger.info("AI enhancement completed for agent={agent_id}", agent_id=agent_id)
    return {"enhanced_content": enhanced}
