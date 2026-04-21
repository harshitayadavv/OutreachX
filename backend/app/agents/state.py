"""
OutreachX — AgentState
----------------------
Single shared object that flows through every LangGraph node.
Each node reads from it and returns a partial dict to update it.
"""

from typing import TypedDict, Optional, Literal


class Lead(TypedDict, total=False):
    # Core identity
    company_name:  str
    website:       str
    country:       str
    industry:      str
    description:   str
    founded_year:  Optional[int]
    batch:         Optional[str]
    funding_stage: Optional[str]
    source:        Optional[str]

    # CEO
    ceo_name:             Optional[str]
    ceo_email:            Optional[str]
    ceo_linkedin:         Optional[str]
    ceo_email_source:     Optional[str]
    ceo_email_confidence: Optional[int]

    # CTO
    cto_name:         Optional[str]
    cto_email:        Optional[str]
    cto_linkedin:     Optional[str]
    cto_email_source: Optional[str]

    # HR
    hr_name:         Optional[str]
    hr_email:        Optional[str]
    hr_linkedin:     Optional[str]
    hr_email_source: Optional[str]

    # Research insights
    tech_stack:           Optional[list]
    pain_points:          Optional[list]
    personalization_hook: Optional[str]

    # Attached email (added by main.py for convenience)
    _email: Optional[dict]


class GeneratedEmail(TypedDict, total=False):
    lead_company:         str
    to_name:              str
    to_email:             str
    subject:              str
    body:                 str
    personalization_score: float
    status:               str   # draft | approved | needs_review | skipped_no_email | sent


class Memory(TypedDict, total=False):
    past_queries:     list
    current_plan:     dict
    successful_hooks: list
    failed_patterns:  list


class AgentState(TypedDict, total=False):
    # ── Input ──────────────────────────────────────────────────
    query:              str
    campaign_id:        Optional[str]

    # ── Routing ────────────────────────────────────────────────
    entry_mode:       Literal["discovery", "uploaded_db", "direct"]
    direct_companies: Optional[list]   # company names from direct input
    target_role:      str   # "ceo" | "cto" | "hr" | "engineering"

    # ── File upload (Path B) ───────────────────────────────────
    uploaded_file_path: Optional[str]
    uploaded_file_type: Optional[str]

    # ── Sender identity ────────────────────────────────────────
    sender_name:        Optional[str]
    sender_value_prop:  Optional[str]
    sender_background:  Optional[str]   # from resume

    # ── Pipeline stages ────────────────────────────────────────
    raw_search_results: Optional[list]
    leads:              list            # after discovery
    researched_leads:   list            # after researcher
    enriched_leads:     list            # after contact_finder
    generated_emails:   list            # after email_generator
    validated_emails:   list            # after validator

    # ── Tracking ───────────────────────────────────────────────
    current_step: str
    errors:       list

    # ── Memory ─────────────────────────────────────────────────
    memory: Optional[Memory]