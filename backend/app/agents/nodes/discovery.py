"""
Discovery Node
──────────────
Handles BOTH entry paths:

  Path A — AI discovery:
    Reads the planner's search_queries from memory,
    runs SerpAPI via serp_tool.py, writes leads to state.

  Path B — Uploaded database:
    Reads the temp file path from state,
    parses CSV / Excel / JSON with Pandas,
    maps columns to Lead schema,
    writes leads to state.
    (Skips SerpAPI entirely.)
"""

import os
import json
import pandas as pd
from typing import Optional

from app.agents.state import AgentState, Lead
from app.agents.tools.serp_tool import run_discovery


# ── Column name aliases ───────────────────────────────────────────────────────
# Users upload spreadsheets with all kinds of column names.
# Map common variations → our canonical Lead field names.

COLUMN_ALIASES: dict[str, str] = {
    # company
    "company": "company_name",
    "company name": "company_name",
    "organization": "company_name",
    "org": "company_name",
    "startup": "company_name",

    # website
    "url": "website",
    "domain": "website",
    "site": "website",
    "homepage": "website",

    # contact name
    "name": "ceo_name",
    "founder": "ceo_name",
    "contact": "ceo_name",
    "contact name": "ceo_name",
    "full name": "ceo_name",

    # email
    "email": "ceo_email",
    "email address": "ceo_email",
    "contact email": "ceo_email",
    "founder email": "ceo_email",

    # linkedin
    "linkedin": "ceo_linkedin",
    "linkedin url": "ceo_linkedin",
    "profile": "ceo_linkedin",

    # misc
    "country": "country",
    "location": "country",
    "industry": "industry",
    "sector": "industry",
    "description": "description",
    "about": "description",
    "batch": "batch",
    "founded": "founded_year",
    "year": "founded_year",
}


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase + strip column names, then apply aliases."""
    df.columns = [c.lower().strip() for c in df.columns]
    df = df.rename(columns=COLUMN_ALIASES)
    return df


def row_to_lead(row: dict) -> Optional[Lead]:
    """Convert one spreadsheet row to a Lead dict. Returns None if no company name."""
    company = row.get("company_name", "")
    if not company or pd.isna(company):
        return None

    lead: Lead = {
        "company_name": str(company).strip(),
        "source": "uploaded_db",
    }

    # Copy over any recognised fields that exist in the row
    optional_fields = [
        "website", "country", "industry", "description",
        "founded_year", "batch", "funding_stage",
        "ceo_name", "ceo_email", "ceo_linkedin",
        "cto_name", "cto_email", "cto_linkedin",
        "hr_name", "hr_email", "hr_linkedin",
    ]
    for field in optional_fields:
        val = row.get(field)
        if val and not (isinstance(val, float) and pd.isna(val)):
            lead[field] = str(val).strip() if field != "founded_year" else int(float(val))

    return lead


def parse_uploaded_file(file_path: str, file_type: str) -> list[Lead]:
    """
    Parse a CSV, Excel, or JSON file into a list of Lead dicts.

    Args:
        file_path: absolute path to the temp uploaded file
        file_type: "csv" | "xlsx" | "xls" | "json"

    Returns:
        list of Lead dicts (invalid rows are silently skipped)
    """
    print(f"[Discovery] Parsing uploaded file: {file_path} ({file_type})")

    if file_type in ("xlsx", "xls"):
        df = pd.read_excel(file_path)
    elif file_type == "csv":
        df = None
        for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
            try:
                df = pd.read_csv(file_path, encoding=enc, on_bad_lines="skip")
                break
            except (UnicodeDecodeError, Exception):
                continue
        if df is None:
            raise ValueError("Could not decode CSV — try saving as UTF-8 from Excel")
    elif file_type == "json":
        df = pd.read_json(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    df = normalise_columns(df)

    leads: list[Lead] = []
    for _, row in df.iterrows():
        lead = row_to_lead(row.to_dict())
        if lead:
            leads.append(lead)

    print(f"[Discovery] Parsed {len(leads)} leads from uploaded file")
    return leads


# ── Node function ─────────────────────────────────────────────────────────────

async def discovery_node(state: AgentState) -> dict:
    """
    Reads:  state["entry_mode"], state["memory"]["current_plan"],
            state["uploaded_file_path"], state["uploaded_file_type"]

    Writes: state["leads"], state["raw_search_results"] (Path A only),
            state["current_step"], state["errors"]
    """

    errors = state.get("errors", [])
    entry_mode = state.get("entry_mode", "discovery")

    # ── Path B: Uploaded database ──────────────────────────────────────────────
    if entry_mode == "uploaded_db":
        file_path = state.get("uploaded_file_path")
        file_type = state.get("uploaded_file_type", "csv")

        if not file_path or not os.path.exists(file_path):
            return {
                "leads": [],
                "current_step": "Error: uploaded file not found",
                "errors": errors + ["Uploaded file not found"],
            }

        try:
            leads = parse_uploaded_file(file_path, file_type)
            return {
                "leads": leads,
                "current_step": f"Loaded {len(leads)} leads from your file — generating emails...",
                "errors": errors,
            }
        except Exception as e:
            return {
                "leads": [],
                "current_step": f"Error parsing file: {e}",
                "errors": errors + [str(e)],
            }

    # ── Path A: AI Discovery via SerpAPI ───────────────────────────────────────
    memory = state.get("memory", {})
    plan = memory.get("current_plan", {})

    search_queries = plan.get("search_queries", [])
    max_leads = plan.get("max_leads", 20)

    if not search_queries:
        # Fallback: build a simple query from the raw user query
        query = state.get("query", "startups")
        search_queries = [
            f"{query} list site:ycombinator.com",
            f"{query} startups crunchbase",
            f"{query} companies founders",
        ]

    try:
        raw_leads = await run_discovery(
            search_queries,
            max_leads=max_leads,
            original_query=state.get("query", ""),
        )
    except Exception as e:
        print(f"[Discovery] SerpAPI failed: {e}")
        return {
            "leads": [],
            "raw_search_results": [],
            "current_step": f"Discovery failed: {e}",
            "errors": errors + [str(e)],
        }

    return {
        "leads": raw_leads,
        "raw_search_results": raw_leads,  # keep raw copy for debugging
        "current_step": f"Discovered {len(raw_leads)} leads — researching...",
        "errors": errors,
    }