"""
CRUD operations
---------------
All database read/write operations in one place.
Used by FastAPI route handlers.

Pattern: async functions that take a db session and return ORM objects.
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, CampaignStatus
from app.models.lead     import Lead
from app.models.email    import Email, EmailStatus


# ═════════════════════════════════════════════════════════════════════════════
# Campaign CRUD
# ═════════════════════════════════════════════════════════════════════════════

async def create_campaign(db: AsyncSession, **kwargs) -> Campaign:
    campaign = Campaign(id=str(uuid.uuid4()), **kwargs)
    db.add(campaign)
    await db.flush()
    return campaign


async def get_campaign(db: AsyncSession, campaign_id: str) -> Optional[Campaign]:
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    return result.scalar_one_or_none()


async def list_campaigns(db: AsyncSession, limit: int = 50) -> list[Campaign]:
    result = await db.execute(
        select(Campaign).order_by(Campaign.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def update_campaign_status(
    db: AsyncSession, campaign_id: str, status: CampaignStatus
) -> None:
    await db.execute(
        update(Campaign)
        .where(Campaign.id == campaign_id)
        .values(status=status, updated_at=datetime.utcnow())
    )


async def update_campaign_stats(db: AsyncSession, campaign_id: str) -> None:
    """Recompute denormalised stats from the emails table."""
    from sqlalchemy import case
    result = await db.execute(
        select(
            func.count(Email.id).label("total"),
            func.sum(case((Email.status == EmailStatus.sent, 1), else_=0)).label("sent"),
            func.sum(case((Email.opened_at.isnot(None), 1), else_=0)).label("opened"),
            func.sum(case((Email.clicked_at.isnot(None), 1), else_=0)).label("clicked"),
            func.sum(case((Email.replied_at.isnot(None), 1), else_=0)).label("replied"),
        ).where(Email.campaign_id == campaign_id)
    )
    row = result.one()
    await db.execute(
        update(Campaign)
        .where(Campaign.id == campaign_id)
        .values(
            emails_sent    = row.sent    or 0,
            emails_opened  = row.opened  or 0,
            emails_clicked = row.clicked or 0,
            emails_replied = row.replied or 0,
            updated_at     = datetime.utcnow(),
        )
    )


# ═════════════════════════════════════════════════════════════════════════════
# Lead CRUD
# ═════════════════════════════════════════════════════════════════════════════

async def create_lead(db: AsyncSession, campaign_id: str, lead_data: dict) -> Lead:
    lead = Lead(
        id          = str(uuid.uuid4()),
        campaign_id = campaign_id,
        company_name  = lead_data.get("company_name",""),
        website       = lead_data.get("website"),
        country       = lead_data.get("country"),
        industry      = lead_data.get("industry"),
        description   = lead_data.get("description"),
        founded_year  = lead_data.get("founded_year"),
        batch         = lead_data.get("batch"),
        funding_stage = lead_data.get("funding_stage"),
        source        = lead_data.get("source"),
        ceo_name      = lead_data.get("ceo_name"),
        ceo_email     = lead_data.get("ceo_email"),
        ceo_linkedin  = lead_data.get("ceo_linkedin"),
        ceo_email_source     = lead_data.get("ceo_email_source"),
        ceo_email_confidence = lead_data.get("ceo_email_confidence"),
        cto_name      = lead_data.get("cto_name"),
        cto_email     = lead_data.get("cto_email"),
        cto_linkedin  = lead_data.get("cto_linkedin"),
        cto_email_source = lead_data.get("cto_email_source"),
        hr_name       = lead_data.get("hr_name"),
        hr_email      = lead_data.get("hr_email"),
        hr_linkedin   = lead_data.get("hr_linkedin"),
        hr_email_source = lead_data.get("hr_email_source"),
        tech_stack           = lead_data.get("tech_stack"),
        pain_points          = lead_data.get("pain_points"),
        personalization_hook = lead_data.get("personalization_hook"),
    )
    db.add(lead)
    await db.flush()
    return lead


async def bulk_create_leads(
    db: AsyncSession, campaign_id: str, leads_data: list[dict]
) -> list[Lead]:
    leads = []
    for ld in leads_data:
        lead = await create_lead(db, campaign_id, ld)
        leads.append(lead)
    await db.execute(
        update(Campaign)
        .where(Campaign.id == campaign_id)
        .values(total_leads=len(leads))
    )
    return leads


async def get_leads(
    db: AsyncSession,
    campaign_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Lead]:
    q = select(Lead).order_by(Lead.created_at.desc()).limit(limit).offset(offset)
    if campaign_id:
        q = q.where(Lead.campaign_id == campaign_id)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_lead(db: AsyncSession, lead_id: str) -> Optional[Lead]:
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    return result.scalar_one_or_none()


# ═════════════════════════════════════════════════════════════════════════════
# Email CRUD
# ═════════════════════════════════════════════════════════════════════════════

async def create_email(
    db: AsyncSession, campaign_id: str, lead_id: str, email_data: dict
) -> Email:
    status_str = email_data.get("status","draft")
    try:
        status = EmailStatus(status_str)
    except ValueError:
        status = EmailStatus.draft

    email = Email(
        id          = str(uuid.uuid4()),
        campaign_id = campaign_id,
        lead_id     = lead_id,
        to_name     = email_data.get("to_name",""),
        to_email    = email_data.get("to_email",""),
        subject     = email_data.get("subject",""),
        body        = email_data.get("body",""),
        personalization_score = email_data.get("personalization_score",0.0),
        status      = status,
        followup_num = email_data.get("followup_num",0),
    )
    db.add(email)
    await db.flush()
    return email


async def get_emails(
    db: AsyncSession,
    campaign_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
) -> list[Email]:
    q = select(Email).order_by(Email.created_at.desc()).limit(limit)
    if campaign_id:
        q = q.where(Email.campaign_id == campaign_id)
    if status:
        try:
            q = q.where(Email.status == EmailStatus(status))
        except ValueError:
            pass
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_email_status(
    db: AsyncSession,
    email_id: str,
    status: EmailStatus,
    **kwargs,   # sent_at, opened_at, tracking_id, etc.
) -> None:
    await db.execute(
        update(Email)
        .where(Email.id == email_id)
        .values(status=status, updated_at=datetime.utcnow(), **kwargs)
    )


async def mark_email_sent(
    db: AsyncSession, email_id: str, tracking_id: str, provider_msg_id: str = ""
) -> None:
    await update_email_status(
        db, email_id, EmailStatus.sent,
        tracking_id     = tracking_id,
        provider_msg_id = provider_msg_id,
        sent_at         = datetime.utcnow(),
        followup_scheduled_at = datetime.utcnow(),
    )


async def mark_email_opened(db: AsyncSession, tracking_id: str) -> None:
    await db.execute(
        update(Email)
        .where(Email.tracking_id == tracking_id)
        .values(status=EmailStatus.opened, opened_at=datetime.utcnow())
    )
    await db.flush()


async def mark_email_clicked(db: AsyncSession, tracking_id: str) -> None:
    await db.execute(
        update(Email)
        .where(Email.tracking_id == tracking_id)
        .values(status=EmailStatus.clicked, clicked_at=datetime.utcnow())
    )
    await db.flush()


async def mark_email_replied(db: AsyncSession, tracking_id: str) -> None:
    await db.execute(
        update(Email)
        .where(Email.tracking_id == tracking_id)
        .values(status=EmailStatus.replied, replied_at=datetime.utcnow())
    )
    await db.flush()


async def get_campaign_stats(db: AsyncSession, campaign_id: str) -> dict:
    """Return open/click/reply stats for a campaign."""
    from sqlalchemy import Integer, case
    result = await db.execute(
        select(
            func.count(Email.id).label("total"),
            func.sum(case((Email.sent_at.isnot(None), 1), else_=0)).label("sent"),
            func.sum(case((Email.opened_at.isnot(None), 1), else_=0)).label("opened"),
            func.sum(case((Email.clicked_at.isnot(None), 1), else_=0)).label("clicked"),
            func.sum(case((Email.replied_at.isnot(None), 1), else_=0)).label("replied"),
        ).where(
            Email.campaign_id == campaign_id,
            Email.followup_num == 0,
        )
    )
    row = result.one()
    total  = row.total  or 0
    sent   = row.sent   or 0
    opened = row.opened or 0
    return {
        "total":      total,
        "sent":       sent,
        "opened":     opened,
        "clicked":    row.clicked or 0,
        "replied":    row.replied or 0,
        "open_rate":  round(opened / sent * 100, 1) if sent else 0,
        "click_rate": round((row.clicked or 0) / sent * 100, 1) if sent else 0,
        "reply_rate": round((row.replied or 0) / sent * 100, 1) if sent else 0,
    }