"""Bounded Resend acceptance and webhook delivery evidence."""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Final

from pymongo.errors import DuplicateKeyError


PROVIDER_MESSAGE_COLLECTION: Final = "newsletter_provider_messages"
PROVIDER_EVENT_COLLECTION: Final = "newsletter_provider_events"
SUPPORTED_RESEND_EVENTS: Final = frozenset({
    "email.sent",
    "email.delivered",
    "email.delivery_delayed",
    "email.failed",
    "email.bounced",
    "email.complained",
})


@dataclass(frozen=True)
class IndexDefinition:
    keys: tuple[tuple[str, int], ...]
    name: str
    unique: bool = False


PROVIDER_MESSAGE_INDEXES: Final = (
    IndexDefinition(
        keys=(("provider", 1), ("provider_message_id", 1)),
        name="newsletter_provider_message_unique",
        unique=True,
    ),
    IndexDefinition(
        keys=(("campaign_id", 1), ("accepted_at", 1)),
        name="newsletter_provider_message_campaign",
    ),
)
PROVIDER_EVENT_INDEXES: Final = (
    IndexDefinition(
        keys=(("provider", 1), ("provider_event_id", 1)),
        name="newsletter_provider_event_unique",
        unique=True,
    ),
    IndexDefinition(
        keys=(("campaign_id", 1), ("event_type", 1), ("occurred_at", 1)),
        name="newsletter_provider_event_campaign",
    ),
)


def _utc_datetime(value, field_name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"invalid_{field_name}")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"invalid_{field_name}") from None
    if parsed.tzinfo is None:
        raise ValueError(f"invalid_{field_name}")
    return parsed.astimezone(timezone.utc)


def verify_resend_webhook(raw_body, headers, secret, *, verifier_factory=None):
    """Verify the exact body with Svix before decoding JSON."""
    if not isinstance(secret, str) or not secret.strip():
        raise ValueError("webhook_not_configured")
    required = ("svix-id", "svix-timestamp", "svix-signature")
    safe_headers = {name: headers.get(name) for name in required}
    if not all(isinstance(safe_headers[name], str) and safe_headers[name]
               for name in required):
        raise ValueError("invalid_webhook_signature")
    if verifier_factory is None:
        try:
            from svix.webhooks import Webhook
        except ImportError:
            raise ValueError("webhook_verifier_unavailable") from None
        verifier_factory = Webhook
    try:
        verifier_factory(secret.strip()).verify(raw_body, safe_headers)
    except Exception:
        raise ValueError("invalid_webhook_signature") from None
    try:
        decoded = json.loads(raw_body)
    except (TypeError, UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("malformed_webhook_payload") from None
    if not isinstance(decoded, dict):
        raise ValueError("malformed_webhook_payload")
    return decoded


def normalize_resend_event(payload, provider_event_id, *, received_at=None):
    """Return a bounded event document, or None for unsupported events."""
    if not isinstance(payload, dict):
        raise ValueError("invalid_resend_event")
    event_type = payload.get("type")
    if event_type not in SUPPORTED_RESEND_EVENTS:
        return None
    data = payload.get("data")
    message_id = data.get("email_id") if isinstance(data, dict) else None
    if not isinstance(provider_event_id, str) or not provider_event_id.strip():
        raise ValueError("invalid_resend_event")
    if not isinstance(message_id, str) or not message_id.strip():
        raise ValueError("invalid_resend_event")
    document = {
        "provider": "resend",
        "provider_event_id": provider_event_id.strip(),
        "provider_message_id": message_id.strip(),
        "event_type": event_type,
        "occurred_at": _utc_datetime(payload.get("created_at"), "resend_event_time"),
        "received_at": received_at or datetime.now(timezone.utc),
    }
    if event_type == "email.bounced":
        bounce = data.get("bounce")
        if isinstance(bounce, dict):
            for source, target in (("type", "bounce_type"), ("subType", "bounce_subtype")):
                value = bounce.get(source)
                if isinstance(value, str) and value.strip():
                    document[target] = value.strip()[:80]
    return document


def _state_transition(event_type, message_id):
    """Return a conditional Mongo update that cannot regress a terminal state."""
    query = {"provider": "resend", "provider_message_id": message_id}
    update = None
    if event_type == "email.sent":
        query["delivery_state"] = "accepted"
        update = {"delivery_state": "sent"}
    elif event_type == "email.delivery_delayed":
        query["delivery_state"] = {"$in": ["accepted", "sent", "delayed"]}
        update = {"delivery_state": "delayed"}
    elif event_type == "email.delivered":
        query["delivery_state"] = {"$nin": ["bounced", "failed"]}
        update = {"delivery_state": "delivered"}
    elif event_type == "email.failed":
        query["delivery_state"] = {"$in": ["accepted", "sent", "delayed"]}
        update = {"delivery_state": "failed"}
    elif event_type == "email.bounced":
        update = {"delivery_state": "bounced"}
    elif event_type == "email.complained":
        update = {"complained": True}
    return query, update


class ResendDeliveryEvidenceRepository:
    def __init__(self, messages, events):
        self.messages = messages
        self.events = events

    async def ensure_indexes(self):
        for collection, definitions in (
            (self.messages, PROVIDER_MESSAGE_INDEXES),
            (self.events, PROVIDER_EVENT_INDEXES),
        ):
            for definition in definitions:
                options = {"name": definition.name}
                if definition.unique:
                    options["unique"] = True
                await collection.create_index(list(definition.keys), **options)

    async def _apply_event_state(self, event):
        query, update = _state_transition(
            event["event_type"], event["provider_message_id"]
        )
        if update:
            await self.messages.update_one(query, {"$set": update})

    async def _correlate_retained_events(self, outbound):
        retained = await self.events.find({
            "provider": "resend",
            "provider_message_id": outbound["provider_message_id"],
            "correlated": False,
        }).to_list(1000)
        retained.sort(key=lambda item: item["occurred_at"])
        for event in retained:
            await self.events.update_one(
                {
                    "provider": "resend",
                    "provider_event_id": event["provider_event_id"],
                    "correlated": False,
                },
                {"$set": {
                    "correlated": True,
                    "campaign_id": outbound.get("campaign_id"),
                    "newsletter_family": outbound.get("newsletter_family"),
                    "recipient_id": outbound.get("recipient_id"),
                }},
            )
            await self._apply_event_state(event)

    async def save_acceptances(self, rows, *, accepted_at=None, run_fields=None):
        timestamp = accepted_at or datetime.now(timezone.utc)
        run_fields = dict(run_fields or {})
        saved = 0
        for row in rows or ():
            provider_message_id = row.get("provider_message_id")
            campaign_id = row.get("campaign_id")
            recipient_id = row.get("recipient_id")
            family = row.get("newsletter_family")
            if not all(isinstance(value, str) and value.strip() for value in (
                provider_message_id, campaign_id, recipient_id, family
            )):
                continue
            document = {
                "provider": "resend",
                "provider_message_id": provider_message_id.strip(),
                "campaign_id": campaign_id.strip(),
                "tracking_id": campaign_id.strip(),
                "newsletter_family": family.strip(),
                "recipient_id": recipient_id.strip(),
                "accepted_at": timestamp,
                "delivery_state": "accepted",
                "complained": False,
                **run_fields,
            }
            result = await self.messages.update_one(
                {"provider": "resend", "provider_message_id": document["provider_message_id"]},
                {"$setOnInsert": document},
                upsert=True,
            )
            if getattr(result, "upserted_id", None) is not None:
                saved += 1
            outbound = await self.messages.find_one({
                "provider": "resend",
                "provider_message_id": document["provider_message_id"],
            })
            if outbound:
                await self._correlate_retained_events(outbound)
        return saved

    async def record_event(self, event):
        outbound = await self.messages.find_one({
            "provider": "resend",
            "provider_message_id": event["provider_message_id"],
        })
        document = dict(event)
        if outbound is None:
            document["correlated"] = False
        else:
            document.update({
                "correlated": True,
                "campaign_id": outbound.get("campaign_id"),
                "newsletter_family": outbound.get("newsletter_family"),
                "recipient_id": outbound.get("recipient_id"),
            })
        try:
            await self.events.insert_one(document)
        except DuplicateKeyError:
            return "duplicate"
        if outbound is None:
            return "uncorrelated"
        await self._apply_event_state(event)
        return "recorded"


async def aggregate_campaign_delivery(messages, campaign_id):
    rows = await messages.find({"provider": "resend", "campaign_id": campaign_id}).to_list(100000)
    accepted = len(rows)
    complained = sum(1 for row in rows if row.get("complained") is True)
    return {
        "campaign_id": campaign_id,
        "accepted": accepted,
        "delivered": sum(1 for row in rows if row.get("delivery_state") == "delivered"),
        "delayed": sum(1 for row in rows if row.get("delivery_state") == "delayed"),
        "bounced": sum(1 for row in rows if row.get("delivery_state") == "bounced"),
        "failed": sum(1 for row in rows if row.get("delivery_state") == "failed"),
        "complained": complained,
        "complaint_rate": (complained / accepted) if accepted else 0.0,
        "complaint_rate_denominator": "accepted",
    }
