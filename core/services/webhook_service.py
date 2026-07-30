"""Webhook service: manages callback registration and delivers review-completion notifications."""

import uuid
from datetime import datetime
from uuid import UUID

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from core.models.callback import Callback
from core.models.notification import Notification
from core.models.profile import Profile

log = structlog.get_logger()

# Fixed namespace so notification ids are deterministic across the app's lifetime.
NOTIFICATION_NAMESPACE = uuid.UUID("d3f8a1c4-6b2e-4c1a-9c8f-2b8f8a1e2d3f")
MAX_SEND_ATTEMPTS = 3
SEND_TIMEOUT_SECONDS = 5.0


class ProfileNotFoundError(Exception):
    """Raised when the profile doesn't exist or isn't owned by the requesting user."""


class CallbackAlreadyExistsError(Exception):
    """Raised when a callback is already registered for a profile."""


class WebhookTimeoutError(Exception):
    """Raised when a single delivery attempt to the callback URL times out."""


class RetriesExceededError(Exception):
    """Raised when send_notification exhausts MAX_SEND_ATTEMPTS without a successful delivery."""


async def set_callback_url(db: AsyncSession, user_id: UUID, profile_id: UUID, url: str) -> Callback:
    """
    Create a Callback record for the given user/profile, commit it, and return it.
    Raises ProfileNotFoundError if the profile doesn't exist or isn't owned by user_id.
    Raises CallbackAlreadyExistsError if one is already registered for this profile —
    callers must delete it first before registering a new one.
    """
    profile_stmt = select(Profile).where(
        Profile.id == str(profile_id), Profile.user_id == str(user_id)
    )
    profile_result = await db.execute(profile_stmt)
    if profile_result.scalars().first() is None:
        raise ProfileNotFoundError(f"Profile {profile_id} not found for user {user_id}")

    stmt = select(Callback).where(Callback.profile_id == str(profile_id))
    result = await db.execute(stmt)
    existing = result.scalars().first()

    if existing is not None:
        raise CallbackAlreadyExistsError(f"Callback already registered for profile {profile_id}")

    callback = Callback(
        user_id=str(user_id),
        profile_id=str(profile_id),
        url=url,
    )
    db.add(callback)
    await db.commit()
    await db.refresh(callback)
    return callback


async def delete_callback_url(db: AsyncSession, user_id: UUID, profile_id: UUID) -> bool:
    """
    Delete the Callback registered for this user/profile. Returns True if a row was deleted,
    False if no matching callback exists.
    """
    stmt = select(Callback).where(
        Callback.profile_id == str(profile_id), Callback.user_id == str(user_id)
    )
    result = await db.execute(stmt)
    callback = result.scalars().first()

    if callback is None:
        return False

    await db.delete(callback)
    await db.commit()
    return True


def generate_notification_id(user_id: str, profile_id: str, review_id: str) -> str:
    """Derive a stable notification id from the triple so retries and resends reuse the same id."""
    return str(uuid.uuid5(NOTIFICATION_NAMESPACE, f"{user_id}:{profile_id}:{review_id}"))


async def notify_callback_on_review_completed(
    user_id: str, profile_id: str, review_id: str, callback_id: str, callback_url: str
) -> None:
    """
    Entry point invoked (via asyncio.create_task) from process_review once a review completes,
    with the callback already looked up by process_review (using its own session) so this
    function doesn't need to re-query it. Opens its own database session since it runs detached
    from the caller's request-scoped session and may still be running after process_review
    returns.
    """
    async with AsyncSessionLocal() as db:
        try:
            notification_id = generate_notification_id(
                str(user_id), str(profile_id), str(review_id)
            )
            notification = await create_notification(
                db=db,
                callback_id=callback_id,
                review_id=str(review_id),
                notification_id=notification_id,
            )

            await send_notification(db=db, notification=notification, callback_url=callback_url)

        except RetriesExceededError as exc:
            log.error(
                "notify_callback_on_review_completed_retries_exceeded",
                review_id=str(review_id),
                profile_id=str(profile_id),
                error=str(exc),
            )
        except Exception as exc:
            log.error(
                "notify_callback_on_review_completed_failed",
                review_id=str(review_id),
                profile_id=str(profile_id),
                error=str(exc),
            )


async def create_notification(
    db: AsyncSession, callback_id: str, review_id: str, notification_id: str
) -> Notification:
    """
    Create the Notification record for this event, or reuse the existing one if this is a resend
    (same notification_id) so retries don't create duplicate rows.
    """
    stmt = select(Notification).where(Notification.id == notification_id)
    result = await db.execute(stmt)
    notification: Notification | None = result.scalars().first()

    if notification is None:
        notification = Notification(
            id=notification_id,
            callback_id=callback_id,
            review_id=review_id,
            delivery_status="pending",
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)

    return notification


async def send_notification(
    db: AsyncSession, notification: Notification, callback_url: str
) -> None:
    """
    POST the notification payload to callback_url, retrying up to MAX_SEND_ATTEMPTS times with a
    SEND_TIMEOUT_SECONDS timeout per attempt. Updates delivery_status and raises
    RetriesExceededError if every attempt fails.
    """
    payload = {
        "notification_id": notification.id,
        "review_id": notification.review_id,
        "callback_id": notification.callback_id,
        "event": "review.completed",
    }

    last_error: Exception | None = None

    async with httpx.AsyncClient(timeout=SEND_TIMEOUT_SECONDS) as client:
        for attempt in range(1, MAX_SEND_ATTEMPTS + 1):
            notification.last_sent_at = datetime.utcnow()
            try:
                response = await client.post(callback_url, json=payload)
                response.raise_for_status()

                notification.delivery_status = "success"
                notification.last_ack_at = datetime.utcnow()
                db.add(notification)
                await db.commit()
                log.info("notification_delivered", notification_id=notification.id, attempt=attempt)
                return

            except httpx.TimeoutException as exc:
                last_error = WebhookTimeoutError(str(exc))
                log.warning(
                    "notification_send_timeout", notification_id=notification.id, attempt=attempt
                )
            except Exception as exc:
                last_error = exc
                log.warning(
                    "notification_send_failed",
                    notification_id=notification.id,
                    attempt=attempt,
                    error=str(exc),
                )

    notification.delivery_status = "fail"
    db.add(notification)
    await db.commit()

    log.error(
        "notification_retries_exceeded",
        notification_id=notification.id,
        attempts=MAX_SEND_ATTEMPTS,
    )
    raise RetriesExceededError(
        f"Exceeded {MAX_SEND_ATTEMPTS} attempts delivering notification {notification.id}"
    ) from last_error
