"""
Email model
-----------
One generated email per lead per campaign.
Tracks: draft → approved → sent → opened → clicked → replied
Follow-ups stored as separate rows with followup_num > 0.
"""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text, Float, ForeignKey, Boolean
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base
import enum


class EmailStatus(str, enum.Enum):
    draft          = "draft"
    approved       = "approved"
    needs_review   = "needs_review"
    skipped        = "skipped_no_email"
    sending        = "sending"
    sent           = "sent"
    opened         = "opened"
    clicked        = "clicked"
    replied        = "replied"
    bounced        = "bounced"
    unsubscribed   = "unsubscribed"
    failed         = "failed"


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    lead_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("leads.id", ondelete="CASCADE"), index=True
    )

    # Content
    to_name:  Mapped[str | None] = mapped_column(String(200), nullable=True)
    to_email: Mapped[str]        = mapped_column(String(200))
    subject:  Mapped[str]        = mapped_column(String(500))
    body:     Mapped[str]        = mapped_column(Text)

    # Quality
    personalization_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[EmailStatus] = mapped_column(
        SAEnum(EmailStatus), default=EmailStatus.draft, index=True
    )

    # Follow-up tracking
    followup_num:   Mapped[int]      = mapped_column(Integer, default=0)   # 0=original, 1=first followup
    parent_email_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Send tracking
    tracking_id:  Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    provider_msg_id: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Event timestamps
    sent_at:       Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    opened_at:     Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    clicked_at:    Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    replied_at:    Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    bounced_at:    Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Follow-up scheduling
    followup_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    followup_sent:         Mapped[bool]             = mapped_column(Boolean, default=False)
    followup_count:        Mapped[int]              = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    lead: Mapped["Lead"] = relationship("Lead", back_populates="emails")

    def __repr__(self):
        return f"<Email {self.id} to={self.to_email} status={self.status}>"

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "campaign_id": self.campaign_id,
            "lead_id":     self.lead_id,
            "to_name":     self.to_name,
            "to_email":    self.to_email,
            "subject":     self.subject,
            "body":        self.body,
            "personalization_score": self.personalization_score,
            "status":      self.status,
            "tracking_id": self.tracking_id,
            "followup_num":   self.followup_num,
            "followup_count": self.followup_count,
            "sent_at":     self.sent_at.isoformat()    if self.sent_at    else None,
            "opened_at":   self.opened_at.isoformat()  if self.opened_at  else None,
            "clicked_at":  self.clicked_at.isoformat() if self.clicked_at else None,
            "replied_at":  self.replied_at.isoformat() if self.replied_at else None,
            "created_at":  self.created_at.isoformat() if self.created_at else None,
        }