import uuid

from loguru import logger

from app.broker import broker
from app.core.constants import NotificationType
from app.db.engine import session_context
from app.repositories.notification import NotificationRepository
from app.services.notification import NotificationService


@broker.task
async def send_notification(
    user_id: str,
    notification_type: str,
    data: dict | None = None,
) -> dict:
    """Async wrapper around NotificationService.send_notification."""
    uid = uuid.UUID(user_id)
    ntype = NotificationType(notification_type)
    logger.info(
        "Sending notification {type} to user {user}",
        type=notification_type, user=user_id,
    )

    from app.core.container import Container
    session = Container.session()
    token = session_context.set(session)
    try:
        service = NotificationService(
            notification_repository=Container.notification_repository(),
        )
        await service.send_notification(uid, ntype, data)
        await session.commit()
        return {"success": True}
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
        session_context.reset(token)
