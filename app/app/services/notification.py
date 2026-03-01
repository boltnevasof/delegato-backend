import uuid

from loguru import logger

from app.core.constants import (
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from app.repositories.notification import NotificationRepository


class NotificationService:
    def __init__(self, notification_repository: NotificationRepository) -> None:
        self._repo = notification_repository

    async def send_notification(
        self,
        user_id: uuid.UUID,
        notification_type: NotificationType,
        data: dict | None = None,
    ) -> None:
        channels = self._get_channels_for_type(notification_type)

        for channel in channels:
            notification = await self._repo.create(
                user_id=user_id,
                type=notification_type,
                channel=channel,
                status=NotificationStatus.PENDING,
                content=data,
            )

            try:
                await self._dispatch(channel, user_id, notification_type, data)
                await self._repo.update_status(
                    notification.id, NotificationStatus.SENT,
                )
            except Exception as e:
                logger.error(
                    "Failed to send {type} via {channel} to {user}: {error}",
                    type=notification_type.value,
                    channel=channel.value,
                    user=user_id,
                    error=str(e),
                )
                await self._repo.update_status(
                    notification.id, NotificationStatus.FAILED,
                )

    def _get_channels_for_type(
        self, notification_type: NotificationType,
    ) -> list[NotificationChannel]:
        email_types = {
            NotificationType.PAYMENT_SUCCESS,
            NotificationType.PAYMENT_FAILED,
            NotificationType.SUBSCRIPTION_EXPIRING,
        }
        telegram_types = {
            NotificationType.SERVER_READY,
            NotificationType.SERVER_ERROR,
            NotificationType.AGENT_STOPPED,
        }

        channels = []
        if notification_type in email_types:
            channels.append(NotificationChannel.EMAIL)
        if notification_type in telegram_types:
            channels.append(NotificationChannel.TELEGRAM)
        if not channels:
            channels.append(NotificationChannel.EMAIL)
        return channels

    async def _dispatch(
        self,
        channel: NotificationChannel,
        user_id: uuid.UUID,
        notification_type: NotificationType,
        data: dict | None,
    ) -> None:
        if channel == NotificationChannel.TELEGRAM:
            await self._send_telegram(user_id, notification_type, data)
        elif channel == NotificationChannel.EMAIL:
            await self._send_email(user_id, notification_type, data)

    async def _send_telegram(
        self,
        user_id: uuid.UUID,
        notification_type: NotificationType,
        data: dict | None,
    ) -> None:
        # Stub: Telegram Bot API call via httpx
        logger.info(
            "Telegram notification sent: {type} to {user}",
            type=notification_type.value, user=user_id,
        )

    async def _send_email(
        self,
        user_id: uuid.UUID,
        notification_type: NotificationType,
        data: dict | None,
    ) -> None:
        # Stub: Unisender email call
        logger.info(
            "Email notification sent: {type} to {user}",
            type=notification_type.value, user=user_id,
        )
