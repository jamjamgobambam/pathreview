import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx
import structlog
from sqlalchemy import select
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings
from core.models.profile import Profile
from core.models.review import Review
from core.models.webhook import Webhook
from core.models.webhook_delivery import WebhookDelivery

log = structlog.get_logger()


async def register_webhook(db, user_id: str, url: str) -> tuple[Webhook, str]:
    """Register a new active webhook for a user."""
    normalized_url = _normalize_url(url)

    existing_stmt = select(Webhook).where(Webhook.user_id == user_id, Webhook.url == normalized_url)
    existing_result = await db.execute(existing_stmt)
    if existing_result.scalars().first():
        raise ValueError("Webhook already exists")

    secret = secrets.token_urlsafe(24)

    webhook = Webhook(user_id=user_id, url=normalized_url, secret=secret, is_active=True)
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)

    secret_value = getattr(webhook, "secret", None) or secret
    return webhook, secret_value


async def list_webhooks(db, user_id: str) -> list[Webhook]:
    """Return all active webhooks owned by a user."""
    stmt = (
        select(Webhook)
        .where(Webhook.user_id == user_id, Webhook.is_active.is_(True))
        .order_by(Webhook.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def delete_webhook(db, webhook_id: str, user_id: str) -> bool:
    """Deactivate a webhook registration owned by the user."""
    stmt = select(Webhook).where(Webhook.id == webhook_id, Webhook.user_id == user_id)
    result = await db.execute(stmt)
    webhook = result.scalars().first()

    if not webhook:
        return False

    webhook.is_active = False
    db.add(webhook)
    await db.commit()
    return True


async def deliver_webhook_notification(db, review_id: str) -> None:
    """Send a webhook notification for a completed or failed review."""
    review_stmt = select(Review).where(Review.id == review_id)
    review_result = await db.execute(review_stmt)
    review = review_result.scalars().first()

    if not review:
        return

    profile_stmt = select(Profile).where(Profile.id == review.profile_id)
    profile_result = await db.execute(profile_stmt)
    profile = profile_result.scalars().first()

    if not profile:
        return

    webhook_stmt = (
        select(Webhook)
        .where(Webhook.user_id == profile.user_id, Webhook.is_active.is_(True))
        .order_by(Webhook.created_at.desc())
    )
    webhook_result = await db.execute(webhook_stmt)
    webhooks = list(webhook_result.scalars().all())

    if not webhooks:
        return

    payload = {
        "review_id": str(review.id),
        "status": review.status,
        "sections": review.sections,
        "overall_score": review.overall_score,
        "error_message": review.error_message,
    }

    for webhook in webhooks:
        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            review_id=review.id,
            status="pending",
            attempt_count=0,
            last_attempted_at=datetime.now(UTC),
        )
        db.add(delivery)

        last_error: Exception | None = None
        for attempt in range(1, settings.webhook_max_attempts + 1):
            try:
                status_code = await _send_with_retry(webhook, payload)
                delivery.status = "success"
                delivery.response_status_code = status_code
                delivery.attempt_count = attempt
                delivery.error_message = None
                delivery.last_attempted_at = datetime.now(UTC)
                break
            except Exception as exc:  # pragma: no cover - exercised in tests via patched helper
                last_error = exc
                delivery.attempt_count = attempt
                delivery.last_attempted_at = datetime.now(UTC)
                if attempt >= settings.webhook_max_attempts:
                    delivery.status = "failed"
                    delivery.response_status_code = None
                    delivery.error_message = str(exc)
                    delivery.last_attempted_at = datetime.now(UTC)
                    log.warning(
                        "webhook_delivery_failed",
                        review_id=str(review.id),
                        webhook_id=str(webhook.id),
                        error=str(exc),
                    )

        db.add(delivery)
        await db.commit()
        if last_error and delivery.status != "failed":
            delivery.status = "failed"
            delivery.error_message = str(last_error)
            db.add(delivery)
            await db.commit()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
async def _send_with_retry(webhook: Webhook, payload: dict[str, object]) -> int:
    """Send a payload to a webhook with retries and exponential backoff."""
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(webhook.secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-PathReview-Signature": f"sha256={signature}",
    }

    async with httpx.AsyncClient(timeout=settings.webhook_timeout_seconds) as client:
        response = await client.post(str(webhook.url), content=body, headers=headers)
        if response.status_code >= 400:
            raise RuntimeError(f"Webhook returned {response.status_code}")
        return response.status_code


def _normalize_url(url: str) -> str:
    """Validate and normalize the webhook URL."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Webhook URL must use http or https")
    if not parsed.netloc:
        raise ValueError("Webhook URL is invalid")
    return parsed.geturl()
