import uuid

from loguru import logger

from app.broker import broker
from app.db.engine import session_context
from app.services.ai import AIService


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
        repo = Container.agent_repository()  # noqa: F811
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
