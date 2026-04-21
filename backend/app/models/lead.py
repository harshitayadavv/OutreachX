"""
Lead model
----------
One target company with all discovered info:
  - company identity (name, website, country, industry)
  - contacts: CEO, CTO, HR (email + LinkedIn per role)
  - research insights (hook, tech stack, pain points)
  - outreach status per campaign
"""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )

    # Company identity
    company_name:  Mapped[str]        = mapped_column(String(200))
    website:       Mapped[str | None] = mapped_column(String(500), nullable=True)
    country:       Mapped[str | None] = mapped_column(String(100), nullable=True)
    industry:      Mapped[str | None] = mapped_column(String(200), nullable=True)
    description:   Mapped[str | None] = mapped_column(Text, nullable=True)
    founded_year:  Mapped[int | None] = mapped_column(Integer, nullable=True)
    batch:         Mapped[str | None] = mapped_column(String(20), nullable=True)   # YC S22
    funding_stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source:        Mapped[str | None] = mapped_column(String(50), nullable=True)   # serpapi | yc | uploaded

    # CEO contact
    ceo_name:             Mapped[str | None] = mapped_column(String(200), nullable=True)
    ceo_email:            Mapped[str | None] = mapped_column(String(200), nullable=True)
    ceo_linkedin:         Mapped[str | None] = mapped_column(String(500), nullable=True)
    ceo_email_source:     Mapped[str | None] = mapped_column(String(50), nullable=True)
    ceo_email_confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # CTO contact
    cto_name:         Mapped[str | None] = mapped_column(String(200), nullable=True)
    cto_email:        Mapped[str | None] = mapped_column(String(200), nullable=True)
    cto_linkedin:     Mapped[str | None] = mapped_column(String(500), nullable=True)
    cto_email_source: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # HR contact
    hr_name:         Mapped[str | None] = mapped_column(String(200), nullable=True)
    hr_email:        Mapped[str | None] = mapped_column(String(200), nullable=True)
    hr_linkedin:     Mapped[str | None] = mapped_column(String(500), nullable=True)
    hr_email_source: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Research insights (JSON arrays stored as JSON column)
    tech_stack:           Mapped[list | None] = mapped_column(JSON, nullable=True)
    pain_points:          Mapped[list | None] = mapped_column(JSON, nullable=True)
    personalization_hook: Mapped[str | None]  = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    emails: Mapped[list["Email"]] = relationship(
        "Email", back_populates="lead", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Lead {self.id} '{self.company_name}'>"

    def to_dict(self) -> dict:
        return {
            "id":           self.id,
            "campaign_id":  self.campaign_id,
            "company_name": self.company_name,
            "website":      self.website,
            "country":      self.country,
            "industry":     self.industry,
            "description":  self.description,
            "founded_year": self.founded_year,
            "batch":        self.batch,
            "source":       self.source,
            "ceo_name":     self.ceo_name,
            "ceo_email":    self.ceo_email,
            "ceo_linkedin": self.ceo_linkedin,
            "ceo_email_confidence": self.ceo_email_confidence,
            "cto_name":     self.cto_name,
            "cto_email":    self.cto_email,
            "cto_linkedin": self.cto_linkedin,
            "hr_name":      self.hr_name,
            "hr_email":     self.hr_email,
            "hr_linkedin":  self.hr_linkedin,
            "tech_stack":           self.tech_stack,
            "personalization_hook": self.personalization_hook,
            "created_at":   self.created_at.isoformat() if self.created_at else None,
        }