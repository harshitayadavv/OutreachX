"""Campaign API routes — POST /campaigns, GET /campaigns, POST /campaigns/{id}/send"""

import os, tempfile, uuid
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update as sa_update
from typing import Optional

from app.db.database  import get_db
from app.db.crud      import (create_campaign, get_campaign, list_campaigns,
                               create_lead, create_email, get_emails, get_leads,
                               get_campaign_stats, update_campaign_status, mark_email_sent)
from app.models.campaign import Campaign, CampaignStatus
from app.agents.graph    import graph
from app.agents.tools.resume_parser import parse_resume
from app.services.email_sender import send_campaign_emails
from app.services.tracker      import register_tracking
from app.services.followup     import queue_followup

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("")
async def list_all_campaigns(db: AsyncSession = Depends(get_db)):
    campaigns = await list_campaigns(db)
    return [
        {
            "id": c.id, "name": c.name, "status": c.status,
            "target_role": c.target_role, "total_leads": c.total_leads,
            "emails_sent": c.emails_sent, "emails_opened": c.emails_opened,
            "emails_replied": c.emails_replied,
            "open_rate":  round(c.emails_opened / c.emails_sent * 100, 1) if c.emails_sent else 0,
            "reply_rate": round(c.emails_replied / c.emails_sent * 100, 1) if c.emails_sent else 0,
            "created_at": c.created_at.isoformat(),
        }
        for c in campaigns
    ]


@router.post("")
async def create_and_run_campaign(
    name:              str  = Form(...),
    query:             Optional[str]        = Form(None),
    leads_file:        Optional[UploadFile] = File(None),
    target_role:       str  = Form("ceo"),
    sender_name:       str  = Form("Alex"),
    sender_email:      str  = Form(""),
    sender_value_prop: str  = Form("B2B SaaS growth and developer tooling"),
    resume_file:       Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
):
    """Create campaign, run AI pipeline, save leads + emails to DB."""
    tmp_leads = tmp_resume = None
    initial = {
        "errors": [], "leads": [],
        "sender_name": sender_name, "sender_value_prop": sender_value_prop,
        "sender_background": "", "target_role": target_role,
    }

    if leads_file:
        suffix = os.path.splitext(leads_file.filename)[-1].lower().lstrip(".")
        if suffix not in ("csv","xlsx","xls","json"):
            raise HTTPException(400, f"Unsupported file type .{suffix}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
            tmp.write(await leads_file.read()); tmp_leads = tmp.name
        initial.update({"uploaded_file_path": tmp_leads, "uploaded_file_type": suffix})
    elif query:
        initial["query"] = query.strip()
    else:
        raise HTTPException(400, "Provide 'query' or 'leads_file'")

    if resume_file:
        rsuffix = os.path.splitext(resume_file.filename)[-1].lower().lstrip(".")
        if rsuffix in ("pdf","txt"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{rsuffix}") as tmp:
                tmp.write(await resume_file.read()); tmp_resume = tmp.name
            profile = await parse_resume(tmp_resume, rsuffix)
            if profile.get("name"):
                initial["sender_name"]       = profile["name"]
                initial["sender_background"] = profile.get("background_summary","")
                if profile.get("value_prop"): initial["sender_value_prop"] = profile["value_prop"]

    # Create campaign row
    campaign = await create_campaign(
        db, name=name, query=query, target_role=target_role,
        sender_name=initial["sender_name"], sender_email=sender_email,
        sender_value_prop=initial["sender_value_prop"],
        sender_background=initial["sender_background"],
        status=CampaignStatus.running,
    )

    try:
        result = await graph.ainvoke(initial)
    except Exception as e:
        await update_campaign_status(db, campaign.id, CampaignStatus.draft)
        raise HTTPException(500, f"AI pipeline failed: {e}")
    finally:
        for p in [tmp_leads, tmp_resume]:
            if p:
                try: os.unlink(p)
                except: pass

    enriched = result.get("enriched_leads") or result.get("leads",[])
    emails   = result.get("validated_emails") or result.get("generated_emails",[])
    email_map = {e.get("lead_company","").lower(): e for e in emails}

    # Save to DB
    saved_leads, saved_emails = 0, 0
    for ld in enriched:
        db_lead = await create_lead(db, campaign.id, ld)
        saved_leads += 1
        email_data = email_map.get((ld.get("company_name") or "").lower())
        if email_data and email_data.get("to_email"):
            await create_email(db, campaign.id, db_lead.id, email_data)
            saved_emails += 1

    # Update campaign totals
    await db.execute(
        sa_update(Campaign).where(Campaign.id == campaign.id)
        .values(total_leads=saved_leads, status=CampaignStatus.review)
    )

    return {
        "campaign_id": campaign.id, "name": campaign.name, "status": "review",
        "total_leads": saved_leads, "emails_ready": saved_emails,
        "pipeline": {
            "discovered": len(result.get("leads",[])),
            "enriched":   len(enriched),
            "emails_approved": sum(1 for e in emails if e.get("status")=="approved"),
        },
        "errors": result.get("errors",[]),
    }


@router.get("/{campaign_id}")
async def get_campaign_detail(campaign_id: str, db: AsyncSession = Depends(get_db)):
    c = await get_campaign(db, campaign_id)
    if not c: raise HTTPException(404, "Campaign not found")
    leads  = await get_leads(db, campaign_id=campaign_id)
    emails = await get_emails(db, campaign_id=campaign_id)
    return {
        "campaign": {
            "id": c.id, "name": c.name, "status": c.status,
            "target_role": c.target_role, "sender_name": c.sender_name,
            "total_leads": c.total_leads, "emails_sent": c.emails_sent,
            "emails_opened": c.emails_opened, "emails_replied": c.emails_replied,
            "created_at": c.created_at.isoformat(),
        },
        "leads":  [l.to_dict() for l in leads],
        "emails": [e.to_dict() for e in emails],
    }


@router.get("/{campaign_id}/stats")
async def campaign_stats(campaign_id: str, db: AsyncSession = Depends(get_db)):
    c = await get_campaign(db, campaign_id)
    if not c: raise HTTPException(404, "Campaign not found")
    return await get_campaign_stats(db, campaign_id)


@router.post("/{campaign_id}/send")
async def send_campaign(
    campaign_id: str,
    dry_run: bool = Form(True),
    db: AsyncSession = Depends(get_db),
):
    """Send all approved emails for this campaign."""
    c = await get_campaign(db, campaign_id)
    if not c: raise HTTPException(404, "Campaign not found")

    emails = await get_emails(db, campaign_id=campaign_id, status="approved")
    if not emails:
        return {"message": "No approved emails to send", "sent": 0}

    email_dicts = [dict(e.to_dict(), status="approved") for e in emails]
    results = await send_campaign_emails(
        emails=email_dicts, from_name=c.sender_name or "OutreachX",
        campaign_id=campaign_id, delay_seconds=2.0, dry_run=dry_run,
    )

    sent_ok = 0
    for email_obj, res in zip(emails, results):
        if res.get("success"):
            tid = res["tracking_id"]
            await mark_email_sent(db, email_obj.id, tid, res.get("provider_msg_id",""))
            register_tracking(tid, campaign_id, email_obj.lead_id, email_obj.to_email)
            queue_followup(
                tracking_id=tid, to_email=email_obj.to_email,
                to_name=email_obj.to_name or "", company=email_obj.to_email.split("@")[-1],
                original_subject=email_obj.subject, hook=email_obj.body[:100],
                sender_name=c.sender_name or "OutreachX",
                value_prop=c.sender_value_prop or "",
            )
            sent_ok += 1

    await update_campaign_status(db, campaign_id, CampaignStatus.active)
    return {
        "campaign_id": campaign_id, "sent": sent_ok,
        "failed": len(results) - sent_ok,
        "followups_queued": sent_ok, "dry_run": dry_run,
    }


@router.patch("/{campaign_id}/email/{email_id}")
async def update_email(
    campaign_id: str, email_id: str,
    action: str = Form(...),   # "approve" | "skip" | "edit"
    subject: Optional[str] = Form(None),
    body:    Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Approve, skip, or edit a generated email before sending."""
    from app.models.email import Email, EmailStatus
    updates = {"updated_at": __import__("datetime").datetime.utcnow()}
    if action == "approve":
        updates["status"] = EmailStatus.approved
    elif action == "skip":
        updates["status"] = EmailStatus.skipped
    elif action == "edit":
        if subject: updates["subject"] = subject
        if body:    updates["body"]    = body
        updates["status"] = EmailStatus.approved
    await db.execute(sa_update(Email).where(Email.id == email_id).values(**updates))
    return {"updated": True, "action": action, "email_id": email_id}