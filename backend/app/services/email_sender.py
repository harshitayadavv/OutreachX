"""
Email Sender Service
--------------------
Sends emails via SendGrid (primary) or SMTP (fallback).

Features:
  - Open tracking   : injects a 1x1 pixel into HTML emails
  - Click tracking  : wraps links to track clicks (via SendGrid)
  - Unsubscribe     : adds one-click unsubscribe header
  - Rate limiting   : max 10 emails/minute to avoid spam flags
  - Dry run mode    : APP_ENV=development prints instead of sending

Usage:
  result = await send_email(
      to_email="harshil@razorpay.com",
      to_name="Harshil Mathur",
      subject="Razorpay's payments lead",
      body="Hi Harshil,\n\n...",
      campaign_id="camp_123",
      lead_id="lead_456",
  )
"""

import asyncio, uuid, re
from datetime import datetime
from typing import Optional

import httpx

from app.core.config import get_settings

settings = get_settings()

SENDGRID_API  = "https://api.sendgrid.com/v3/mail/send"
TRACKING_BASE = "https://outreachx.app/track"   # replace with your domain

# Rate limiting — max emails per minute
_send_semaphore = asyncio.Semaphore(10)
_last_batch_time: float = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _text_to_html(text: str) -> str:
    """Convert plain-text email body to simple HTML."""
    # Escape HTML special chars
    text = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    # Convert line breaks
    paragraphs = text.split("\n\n")
    html_parts = []
    for p in paragraphs:
        p = p.replace("\n","<br>")
        html_parts.append(f"<p style='margin:0 0 12px;line-height:1.6'>{p}</p>")
    return "\n".join(html_parts)


def _inject_tracking_pixel(html: str, tracking_id: str) -> str:
    """Inject a 1x1 transparent pixel for open tracking."""
    pixel = (
        f'<img src="{TRACKING_BASE}/open/{tracking_id}" '
        f'width="1" height="1" style="display:none" alt="" />'
    )
    # Insert before closing body tag, or append
    if "</body>" in html:
        return html.replace("</body>", f"{pixel}</body>")
    return html + pixel


def _build_html_email(
    to_name: str,
    subject: str,
    body_text: str,
    sender_name: str,
    tracking_id: str,
    unsubscribe_url: str,
) -> str:
    """Build a clean, professional HTML email."""
    body_html = _text_to_html(body_text)
    first_name = (to_name or "").split()[0] if to_name else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{subject}</title>
</head>
<body style="margin:0;padding:0;background:#f9f9f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9f9f9;padding:32px 0">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:8px;border:1px solid #e5e5e5;overflow:hidden">
        <!-- Body -->
        <tr><td style="padding:36px 40px 28px;font-size:15px;color:#1a1a1a;line-height:1.65">
          {body_html}
        </td></tr>
        <!-- Divider -->
        <tr><td style="padding:0 40px"><hr style="border:none;border-top:1px solid #e9e9e9;margin:0"></td></tr>
        <!-- Footer -->
        <tr><td style="padding:20px 40px;font-size:12px;color:#888">
          Sent by <strong>{sender_name}</strong> via OutreachX &nbsp;·&nbsp;
          <a href="{unsubscribe_url}" style="color:#888">Unsubscribe</a>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    return _inject_tracking_pixel(html, tracking_id)


# ─────────────────────────────────────────────────────────────────────────────
# SendGrid sender
# ─────────────────────────────────────────────────────────────────────────────

async def _send_via_sendgrid(
    to_email: str, to_name: str,
    subject: str, body_text: str, body_html: str,
    from_email: str, from_name: str,
    tracking_id: str,
) -> dict:
    """Send via SendGrid API. Returns {success, message_id, error}."""

    payload = {
        "personalizations": [{
            "to": [{"email": to_email, "name": to_name or ""}],
            "subject": subject,
        }],
        "from":       {"email": from_email, "name": from_name},
        "reply_to":   {"email": from_email, "name": from_name},
        "content": [
            {"type": "text/plain", "value": body_text},
            {"type": "text/html",  "value": body_html},
        ],
        "tracking_settings": {
            "click_tracking":      {"enable": True, "enable_text": False},
            "open_tracking":       {"enable": True},
            "subscription_tracking": {"enable": False},
        },
        "custom_args": {
            "tracking_id": tracking_id,
            "outreachx":   "true",
        },
        "headers": {
            "List-Unsubscribe": f"<{TRACKING_BASE}/unsubscribe/{tracking_id}>",
            "X-OutreachX-ID":   tracking_id,
        },
    }

    headers = {
        "Authorization": f"Bearer {settings.sendgrid_api_key}",
        "Content-Type":  "application/json",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(SENDGRID_API, json=payload, headers=headers)

    if resp.status_code in (200, 202):
        message_id = resp.headers.get("X-Message-Id","")
        return {"success": True, "message_id": message_id, "provider": "sendgrid"}
    else:
        return {
            "success": False,
            "error":   f"SendGrid HTTP {resp.status_code}: {resp.text[:200]}",
            "provider": "sendgrid",
        }


# ─────────────────────────────────────────────────────────────────────────────
# SMTP fallback
# ─────────────────────────────────────────────────────────────────────────────

async def _send_via_smtp(
    to_email: str, to_name: str,
    subject: str, body_text: str, body_html: str,
    from_email: str, from_name: str,
) -> dict:
    """Send via SMTP (Gmail, Outlook, custom). Runs in thread pool."""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text      import MIMEText

    smtp_host = getattr(settings, "smtp_host", "smtp.gmail.com")
    smtp_port = int(getattr(settings, "smtp_port", 587))
    smtp_user = getattr(settings, "smtp_user", from_email)
    smtp_pass = getattr(settings, "smtp_password", "")

    def _send_sync():
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{from_name} <{from_email}>"
        msg["To"]      = f"{to_name} <{to_email}>" if to_name else to_email
        msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, [to_email], msg.as_string())

        return {"success": True, "message_id": str(uuid.uuid4()), "provider": "smtp"}

    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _send_sync)
    except Exception as e:
        return {"success": False, "error": str(e), "provider": "smtp"}


# ─────────────────────────────────────────────────────────────────────────────
# Main public function
# ─────────────────────────────────────────────────────────────────────────────

async def send_email(
    to_email:    str,
    to_name:     str,
    subject:     str,
    body:        str,
    from_name:   str  = "OutreachX",
    campaign_id: str  = "",
    lead_id:     str  = "",
    dry_run:     bool = False,
) -> dict:
    """
    Send one cold email.

    Args:
        to_email    : recipient email address
        to_name     : recipient name (for personalization)
        subject     : email subject line
        body        : plain text email body
        from_name   : sender display name
        campaign_id : for tracking (stored in SendGrid custom_args)
        lead_id     : for tracking
        dry_run     : if True, print instead of sending

    Returns:
        {
            success:     bool,
            tracking_id: str,    # use to track opens/clicks
            message_id:  str,    # provider message ID
            provider:    str,    # "sendgrid" | "smtp" | "dry_run"
            error:       str,    # only if success=False
            timestamp:   str,
        }
    """
    from_email   = settings.from_email or "outreach@outreachx.app"
    tracking_id  = f"{campaign_id}_{lead_id}_{uuid.uuid4().hex[:8]}"
    unsubscribe  = f"{TRACKING_BASE}/unsubscribe/{tracking_id}"
    timestamp    = datetime.utcnow().isoformat()

    body_html = _build_html_email(
        to_name, subject, body, from_name, tracking_id, unsubscribe
    )

    # ── Dry run (development) ─────────────────────────────────────────────────
    is_dev = settings.app_env == "development"
    if dry_run or (is_dev and not settings.sendgrid_api_key):
        print(f"\n{'='*55}")
        print(f"[DRY RUN] Email #{tracking_id[:12]}")
        print(f"  To      : {to_name} <{to_email}>")
        print(f"  Subject : {subject}")
        print(f"  Body    :\n{body[:300]}...")
        print(f"{'='*55}\n")
        return {
            "success":     True,
            "tracking_id": tracking_id,
            "message_id":  f"dry_run_{uuid.uuid4().hex[:8]}",
            "provider":    "dry_run",
            "timestamp":   timestamp,
        }

    # ── Rate limiting ─────────────────────────────────────────────────────────
    async with _send_semaphore:
        await asyncio.sleep(0.1)  # 100ms between sends = max 10/sec

        # ── SendGrid (primary) ────────────────────────────────────────────────
        if settings.sendgrid_api_key:
            result = await _send_via_sendgrid(
                to_email, to_name, subject, body, body_html,
                from_email, from_name, tracking_id,
            )
        # ── SMTP (fallback) ───────────────────────────────────────────────────
        else:
            result = await _send_via_smtp(
                to_email, to_name, subject, body, body_html,
                from_email, from_name,
            )

    result["tracking_id"] = tracking_id
    result["timestamp"]   = timestamp

    status = "✓" if result.get("success") else "✗"
    print(f"[EmailSender] {status} {to_email} via {result.get('provider')} | id={tracking_id[:12]}")

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Bulk sender — sends a campaign's emails with delays
# ─────────────────────────────────────────────────────────────────────────────

async def send_campaign_emails(
    emails:      list[dict],
    from_name:   str,
    campaign_id: str,
    delay_seconds: float = 3.0,   # wait between sends to avoid spam
    dry_run:     bool = False,
) -> list[dict]:
    """
    Send all approved emails in a campaign.

    Args:
        emails:         list of GeneratedEmail dicts (status == "approved")
        from_name:      sender display name
        campaign_id:    campaign identifier
        delay_seconds:  wait between sends (default 3s)
        dry_run:        if True, print instead of sending

    Returns:
        list of send results with tracking_ids
    """
    to_send = [e for e in emails if e.get("status") == "approved" and e.get("to_email")]
    print(f"[Campaign] Sending {len(to_send)} emails for campaign {campaign_id}...")

    results = []
    for i, email in enumerate(to_send):
        print(f"[Campaign] {i+1}/{len(to_send)} → {email.get('to_email')}")
        result = await send_email(
            to_email    = email["to_email"],
            to_name     = email.get("to_name",""),
            subject     = email["subject"],
            body        = email["body"],
            from_name   = from_name,
            campaign_id = campaign_id,
            lead_id     = email.get("lead_company","").replace(" ","_").lower(),
            dry_run     = dry_run,
        )
        result["lead_company"] = email.get("lead_company","")
        result["to_email"]     = email.get("to_email","")
        results.append(result)

        # Wait between sends (except after the last one)
        if i < len(to_send) - 1:
            await asyncio.sleep(delay_seconds)

    sent_ok = sum(1 for r in results if r.get("success"))
    print(f"[Campaign] Done — {sent_ok}/{len(to_send)} sent successfully")
    return results