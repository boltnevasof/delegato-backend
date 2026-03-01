from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select

from app.broker import broker
from app.core.constants import SubscriptionStatus
from app.db.engine import async_session_factory
from app.models.subscription import Subscription
from app.repositories.otp import OTPCodeRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.subscription import SubscriptionRepository
from app.repositories.tariff import TariffRepository
from app.services.subscription import SubscriptionService


@broker.task(schedule=[{"cron": "0 8 * * *"}])
async def check_subscription_renewals() -> dict:
    """Daily 8 AM: find subscriptions due for renewal and enqueue charges."""
    from app.tasks.payments import process_auto_renewal

    now = datetime.now(timezone.utc)
    count = 0

    async with async_session_factory() as session:
        result = await session.execute(
            select(Subscription).where(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.current_period_end <= now,
            ),
        )
        due_subs = result.scalars().all()

        for sub in due_subs:
            await process_auto_renewal.kiq(str(sub.id))
            count += 1

    logger.info("Enqueued {count} subscription renewals", count=count)
    return {"renewals_enqueued": count}


@broker.task(schedule=[{"cron": "0 9 * * *"}])
async def send_renewal_reminders() -> dict:
    """Daily 9 AM: send reminders for subscriptions expiring in 3 days."""
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    threshold = now + timedelta(days=3)
    count = 0

    async with async_session_factory() as session:
        result = await session.execute(
            select(Subscription).where(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.current_period_end <= threshold,
                Subscription.current_period_end > now,
            ),
        )
        expiring = result.scalars().all()

        for sub in expiring:
            # Stub: enqueue notification task
            logger.info("Renewal reminder for subscription {id}", id=sub.id)
            count += 1

    logger.info("Sent {count} renewal reminders", count=count)
    return {"reminders_sent": count}


@broker.task(schedule=[{"cron": "0 * * * *"}])
async def expire_grace_periods() -> dict:
    """Hourly: expire subscriptions past grace period, stop agents."""
    now = datetime.now(timezone.utc)
    count = 0

    async with async_session_factory() as session:
        sub_repo = SubscriptionRepository(session)
        tariff_repo = TariffRepository(session)
        sub_service = SubscriptionService(
            subscription_repository=sub_repo,
            tariff_repository=tariff_repo,
        )

        result = await session.execute(
            select(Subscription).where(
                Subscription.status.in_([
                    SubscriptionStatus.CANCELLED,
                    SubscriptionStatus.GRACE_PERIOD,
                ]),
                Subscription.grace_period_end <= now,
            ),
        )
        expired = result.scalars().all()

        for sub in expired:
            await sub_service.expire_grace_period(sub.id)
            count += 1

        await session.commit()

    logger.info("Expired {count} grace period subscriptions", count=count)
    return {"expired": count}


@broker.task(schedule=[{"cron": "0 */6 * * *"}])
async def cleanup_expired_tokens() -> dict:
    """Every 6 hours: delete expired OTPs and refresh tokens."""
    async with async_session_factory() as session:
        otp_repo = OTPCodeRepository(session)
        token_repo = RefreshTokenRepository(session)

        otp_count = await otp_repo.delete_expired()
        token_count = await token_repo.delete_expired()
        await session.commit()

    logger.info(
        "Cleaned up {otp} OTPs and {tokens} refresh tokens",
        otp=otp_count, tokens=token_count,
    )
    return {"otps_deleted": otp_count, "tokens_deleted": token_count}
