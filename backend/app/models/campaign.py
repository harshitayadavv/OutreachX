"""
Campaign model
--------------
A campaign is one outreach run:
  - user sets a query or uploads leads
  - AI discovers, researches, generates emails
  - user reviews and sends
"""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base
import enum


class CampaignStatus(str, enum.Enum):
    draft      = "draft"       # created, not sent
    running    = "running"     # AI pipeline in progress
    review     = "review"      # emails ready for user review
    sending    = "sending"     # emails being sent
    active     = "active"      # sent, tracking replies/opens
    completed  = "completed"   # all follow-ups done
    paused     = "paused"


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name:         Mapped[str]           = mapped_column(String(200))
    query:        Mapped[str | None]    = mapped_column(Text, nullable=True)
    target_role:  Mapped[str]           = mapped_column(String(50), default="ceo")
    status:       Mapped[CampaignStatus] = mapped_column(
        SAEnum(CampaignStatus), default=CampaignStatus.draft
    )

    # Sender info
    sender_name:       Mapped[str | None] = mapped_column(String(200), nullable=True)
    sender_email:      Mapped[str | None] = mapped_column(String(200), nullable=True)
    sender_value_prop: Mapped[str | None] = mapped_column(Text, nullable=True)
    sender_background: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Stats (denormalised for fast dashboard queries)
    total_leads:    Mapped[int] = mapped_column(Integer, default=0)
    emails_sent:    Mapped[int] = mapped_column(Integer, default=0)
    emails_opened:  Mapped[int] = mapped_column(Integer, default=0)
    emails_clicked: Mapped[int] = mapped_column(Integer, default=0)
    emails_replied: Mapped[int] = mapped_column(Integer, default=0)

    # Follow-up config
    followup_after_days: Mapped[int] = mapped_column(Integer, default=3)
    max_followups:       Mapped[int] = mapped_column(Integer, default=2)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Campaign {self.id} '{self.name}' [{self.status}]>"