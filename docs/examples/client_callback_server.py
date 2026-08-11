"""Example client callback server: receives PathReview review-completed webhook notifications,
dedupes by notification_id, and can register/delete its own callback URL.

See docs/CLIENT_SETUP.md for setup and usage instructions.
"""

from typing import Any

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

app = FastAPI(title="Example PathReview Callback Client")

# In-memory dedup set. A real client would persist this (e.g. a unique index on
# notification_id in its own DB) so dedup survives a restart.
_seen_notification_ids: set[str] = set()


@app.post("/callback")
async def receive_notification(request: Request) -> dict:
    """Receive a review-completed notification and acknowledge it."""
    payload = await request.json()
    notification_id = payload["notification_id"]

    if notification_id in _seen_notification_ids:
        print(f"[dedup] already processed notification_id={notification_id}, skipping")
        return {"ok": True}

    # Do the real work here (e.g. notify a user, update a record). This is a
    # placeholder standing in for that processing.
    print(
        f"[received] notification_id={notification_id} "
        f"review_id={payload['review_id']} callback_id={payload['callback_id']} "
        f"event={payload['event']}"
    )
    _seen_notification_ids.add(notification_id)

    return {"ok": True}


class CallbackRegistrationRequest(BaseModel):
    pathreview_base_url: str
    token: str
    profile_id: str
    # This server's own publicly reachable /callback URL, e.g. "http://localhost:9000/callback".
    callback_url: str = "http://localhost:9000/callback"


@app.post("/register-callback")
async def register_callback(body: CallbackRegistrationRequest) -> dict:
    """Register this server's /callback URL with PathReview for a profile. Proxies to
    POST /webhooks/callbacks (see api/routes/webhooks.py)."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{body.pathreview_base_url}/webhooks/callbacks",
            headers={"Authorization": f"Bearer {body.token}"},
            json={"profile_id": body.profile_id, "url": body.callback_url},
        )

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    data: dict[str, Any] = response.json()
    return data


class CallbackDeletionRequest(BaseModel):
    pathreview_base_url: str
    token: str
    profile_id: str


@app.delete("/delete-callback")
async def delete_callback(body: CallbackDeletionRequest) -> dict:
    """Delete this profile's registered callback from PathReview. Proxies to
    DELETE /webhooks/callbacks/{profile_id} (see api/routes/webhooks.py)."""
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{body.pathreview_base_url}/webhooks/callbacks/{body.profile_id}",
            headers={"Authorization": f"Bearer {body.token}"},
        )

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
