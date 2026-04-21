"""
Email Tracking Service
----------------------
Tracks email events via URL-based endpoints:

  GET /track/open/{tracking_id}    → records open, returns 1x1 pixel
  GET /track/click/{tracking_id}   → records click, redirects to URL
  GET /track/unsubscribe/{id}      → marks as unsubscribed

In Phase 3 (database), these write to the EmailEvent table.
Right now they write to an in-memory store + log file.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

# In-memory store (replaced by DB in Phase 3)
_events: list[dict] = []
_tracking_map: dict = {}   # tracking_id → {campaign_id, lead_id, email}


def register_tracking(
    tracking_id: str,
    campaign_id: str,
    lead_id:     str,
    to_email:    str,
) -> None:
    """Register a tracking ID before sending."""
    _tracking_map[tracking_id] = {
        "campaign_id": campaign_id,
        "lead_id":     lead_id,
        "to_email":    to_email,
        "status":      "sent",
        "sent_at":     datetime.utcnow().isoformat(),
        "opened_at":   None,
        "clicked_at":  None,
        "replied":     False,
        "unsubscribed": False,
    }


def record_event(tracking_id: str, event_type: str, meta: dict = {}) -> dict:
    """Record an email event and update status."""
    now = datetime.utcnow().isoformat()
    event = {
        "id":          str(uuid.uuid4()),
        "tracking_id": tracking_id,
        "event_type":  event_type,   # "open" | "click" | "unsubscribe" | "reply"
        "timestamp":   now,
        **meta,
    }
    _events.append(event)

    # Update tracking map
    if tracking_id in _tracking_map:
        record = _tracking_map[tracking_id]
        if event_type == "open" and not record.get("opened_at"):
            record["opened_at"] = now
            record["status"]    = "opened"
        elif event_type == "click":
            record["clicked_at"] = now
            record["status"]     = "clicked"
        elif event_type == "reply":
            record["replied"] = True
            record["status"]  = "replied"
        elif event_type == "unsubscribe":
            record["unsubscribed"] = True
            record["status"]       = "unsubscribed"

    print(f"[Tracker] {event_type.upper()} — {tracking_id[:16]} at {now}")
    return event


def get_stats(campaign_id: Optional[str] = None) -> dict:
    """Return email stats for a campaign or all campaigns."""
    records = list(_tracking_map.values())
    if campaign_id:
        records = [r for r in records if r.get("campaign_id") == campaign_id]

    total       = len(records)
    sent        = total
    opened      = sum(1 for r in records if r.get("opened_at"))
    clicked     = sum(1 for r in records if r.get("clicked_at"))
    replied     = sum(1 for r in records if r.get("replied"))
    unsubscribed = sum(1 for r in records if r.get("unsubscribed"))

    return {
        "total":            total,
        "sent":             sent,
        "opened":           opened,
        "clicked":          clicked,
        "replied":          replied,
        "unsubscribed":     unsubscribed,
        "open_rate":        round(opened  / sent * 100, 1) if sent else 0,
        "click_rate":       round(clicked / sent * 100, 1) if sent else 0,
        "reply_rate":       round(replied / sent * 100, 1) if sent else 0,
    }


def get_tracking_record(tracking_id: str) -> Optional[dict]:
    return _tracking_map.get(tracking_id)


def get_all_events() -> list[dict]:
    return list(_events)