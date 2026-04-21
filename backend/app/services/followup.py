"""
Follow-up Scheduler Service
----------------------------
Auto-generates and queues follow-up emails for leads
that haven't replied after N days.

Architecture:
  - APScheduler runs a background job every hour
  - Checks all sent emails in the tracking store
  - If no reply after `followup_after_days`, generates a follow-up
  - Follow-up emails are shorter, reference the original email
  - Max 2 follow-ups per lead (configurable)

In Phase 3 (database), this reads from the Email table.
Right now it works with the in-memory tracker.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval  import IntervalTrigger

from app.services.tracker    import get_all_events, get_tracking_record, record_event
from app.services.email_sender import send_email
from app.core.config         import get_settings

settings = get_settings()

# Follow-up config
FOLLOWUP_AFTER_DAYS = 3    # wait 3 days before first follow-up
MAX_FOLLOWUPS       = 2    # max 2 follow-ups per lead
FOLLOWUP_GAP_DAYS   = 4    # wait 4 more days for second follow-up

# In-memory store of follow-up state (replaced by DB in Phase 3)
# format: {tracking_id: {count: int, last_sent: datetime, original_email: dict}}
_followup_state: dict = {}

# Pending follow-up queue
_followup_queue: list[dict] = []

scheduler: Optional[AsyncIOScheduler] = None


# ─────────────────────────────────────────────────────────────────────────────
# Follow-up email generator
# ─────────────────────────────────────────────────────────────────────────────

FOLLOWUP_TEMPLATES = [
    # Follow-up #1 — short, gentle nudge
    {
        "subject_prefix": "Re: ",
        "body": (
            "Hi {first_name},\n\n"
            "Just following up on my note about {company} — wanted to make sure it didn't get buried.\n\n"
            "{hook}\n\n"
            "Would a quick 15-min call make sense this week?\n\n"
            "Best,\n{sender_name}"
        ),
    },
    # Follow-up #2 — breakup email
    {
        "subject_prefix": "Re: ",
        "body": (
            "Hi {first_name},\n\n"
            "I'll keep this short — I've reached out twice and I don't want to be a bother.\n\n"
            "If the timing isn't right, no worries at all. "
            "But if {company}'s team ever needs help with {value_prop}, I'd love to connect.\n\n"
            "Best,\n{sender_name}"
        ),
    },
]


def _generate_followup_body(
    followup_num:  int,
    first_name:    str,
    company:       str,
    original_subject: str,
    hook:          str,
    sender_name:   str,
    value_prop:    str,
) -> tuple[str, str]:
    """Returns (subject, body) for a follow-up email."""
    template = FOLLOWUP_TEMPLATES[min(followup_num - 1, len(FOLLOWUP_TEMPLATES) - 1)]

    subject = template["subject_prefix"] + original_subject
    body    = template["body"].format(
        first_name  = first_name or "there",
        company     = company,
        hook        = hook,
        sender_name = sender_name,
        value_prop  = value_prop,
    )
    return subject, body


# ─────────────────────────────────────────────────────────────────────────────
# Queue a follow-up manually (called by API or after send)
# ─────────────────────────────────────────────────────────────────────────────

def queue_followup(
    tracking_id:      str,
    to_email:         str,
    to_name:          str,
    company:          str,
    original_subject: str,
    hook:             str,
    sender_name:      str,
    value_prop:       str,
    send_after_days:  int = FOLLOWUP_AFTER_DAYS,
) -> None:
    """Queue a follow-up to be sent after N days if no reply."""
    send_after = datetime.utcnow() + timedelta(days=send_after_days)

    if tracking_id not in _followup_state:
        _followup_state[tracking_id] = {
            "count":    0,
            "last_sent": None,
            "to_email":  to_email,
            "to_name":   to_name,
            "company":   company,
            "original_subject": original_subject,
            "hook":      hook,
            "sender_name": sender_name,
            "value_prop":  value_prop,
        }

    state = _followup_state[tracking_id]

    if state["count"] >= MAX_FOLLOWUPS:
        print(f"[Followup] Max follow-ups reached for {to_email}")
        return

    _followup_queue.append({
        "tracking_id":  tracking_id,
        "send_after":   send_after,
        "followup_num": state["count"] + 1,
    })
    print(f"[Followup] Queued follow-up #{state['count']+1} for {to_email} → send after {send_after.date()}")


# ─────────────────────────────────────────────────────────────────────────────
# Scheduler job — runs every hour
# ─────────────────────────────────────────────────────────────────────────────

async def _process_followup_queue() -> None:
    """Check the queue and send any follow-ups that are due."""
    now = datetime.utcnow()
    due = [f for f in _followup_queue if f["send_after"] <= now]

    if not due:
        return

    print(f"[Followup] Processing {len(due)} due follow-ups...")

    for item in due:
        tracking_id  = item["tracking_id"]
        followup_num = item["followup_num"]
        state        = _followup_state.get(tracking_id, {})

        # Check if they replied — if so, skip
        record = get_tracking_record(tracking_id)
        if record and record.get("replied"):
            print(f"[Followup] {state.get('to_email')} replied — skipping follow-up")
            _followup_queue.remove(item)
            continue

        if record and record.get("unsubscribed"):
            print(f"[Followup] {state.get('to_email')} unsubscribed — skipping")
            _followup_queue.remove(item)
            continue

        # Generate follow-up
        first_name = (state.get("to_name","") or "").split()[0]
        subject, body = _generate_followup_body(
            followup_num  = followup_num,
            first_name    = first_name,
            company       = state.get("company",""),
            original_subject = state.get("original_subject",""),
            hook          = state.get("hook",""),
            sender_name   = state.get("sender_name",""),
            value_prop    = state.get("value_prop",""),
        )

        # Send
        result = await send_email(
            to_email    = state["to_email"],
            to_name     = state.get("to_name",""),
            subject     = subject,
            body        = body,
            from_name   = state.get("sender_name","OutreachX"),
            campaign_id = tracking_id,
            lead_id     = state.get("company","").replace(" ","_").lower(),
        )

        if result.get("success"):
            state["count"]     = followup_num
            state["last_sent"] = now.isoformat()
            _followup_queue.remove(item)
            record_event(tracking_id, "followup_sent", {"followup_num": followup_num})
            print(f"[Followup] ✓ Follow-up #{followup_num} sent to {state['to_email']}")

            # Queue next follow-up if we haven't hit the max
            if followup_num < MAX_FOLLOWUPS:
                queue_followup(
                    tracking_id      = tracking_id,
                    to_email         = state["to_email"],
                    to_name          = state.get("to_name",""),
                    company          = state.get("company",""),
                    original_subject = state.get("original_subject",""),
                    hook             = state.get("hook",""),
                    sender_name      = state.get("sender_name",""),
                    value_prop       = state.get("value_prop",""),
                    send_after_days  = FOLLOWUP_GAP_DAYS,
                )
        else:
            print(f"[Followup] ✗ Failed to send to {state['to_email']}: {result.get('error')}")


def get_followup_queue() -> list[dict]:
    """Return current follow-up queue (for API/dashboard)."""
    return [
        {
            **item,
            "send_after": item["send_after"].isoformat(),
            "state":      _followup_state.get(item["tracking_id"],{}),
        }
        for item in _followup_queue
    ]


def get_followup_stats() -> dict:
    total_queued  = len(_followup_queue)
    total_sent    = sum(s.get("count",0) for s in _followup_state.values())
    return {
        "queued":      total_queued,
        "total_sent":  total_sent,
        "leads_tracked": len(_followup_state),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Scheduler lifecycle
# ─────────────────────────────────────────────────────────────────────────────

def start_scheduler() -> AsyncIOScheduler:
    """Start the background scheduler. Call on app startup."""
    global scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _process_followup_queue,
        trigger  = IntervalTrigger(hours=1),
        id       = "followup_check",
        name     = "Check follow-up queue",
        replace_existing = True,
    )
    scheduler.start()
    print("[Scheduler] Follow-up scheduler started — checking every hour")
    return scheduler


def stop_scheduler() -> None:
    """Stop the scheduler. Call on app shutdown."""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        print("[Scheduler] Stopped")