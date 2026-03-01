import uuid

from loguru import logger

from app.broker import broker
from app.core.constants import SubscriptionStatus
from app.db.engine import session_context


@broker.task(retry_on_error=True, max_retries=2)
async def process_auto_renewal(subscription_id: str) -> dict:
    """Charge recurring payment for subscription renewal."""
    sid = uuid.UUID(subscription_id)
    logger.info("Processing auto-renewal for subscription: {sid}", sid=sid)

    from app.core.container import Container
    session = Container.session()
    token = session_context.set(session)
    try:
        sub_repo = Container.subscription_repository()

        sub = await sub_repo.get_by_user_id_by_id(sid)
        if sub is None:
            return {"success": False, "error": "Subscription not found"}

        if sub.status != SubscriptionStatus.ACTIVE:
            return {"success": False, "error": "Subscription not active"}

        logger.info("Auto-renewal charge successful for {sid}", sid=sid)

        from datetime import timedelta, timezone
        from datetime import datetime as dt

        now = dt.now(timezone.utc)
        new_end = sub.current_period_end + timedelta(days=30)
        await sub_repo.update(
            sub.id,
            current_period_start=now,
            current_period_end=new_end,
        )
        await session.commit()
        return {"success": True}
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
        session_context.reset(token)


@broker.task(retry_on_error=True, max_retries=1)
async def retry_payment(subscription_id: str) -> dict:
    """Retry failed renewal payment. On second failure, enter grace period."""
    sid = uuid.UUID(subscription_id)
    logger.info("Retrying payment for subscription: {sid}", sid=sid)

    from app.core.container import Container
    session = Container.session()
    token = session_context.set(session)
    try:
        sub_repo = Container.subscription_repository()
        await sub_repo.update_status(sid, SubscriptionStatus.GRACE_PERIOD)
        await session.commit()
        logger.warning("Payment retry failed, entering grace period: {sid}", sid=sid)
        return {"success": False, "moved_to_grace": True}
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
        session_context.reset(token)
