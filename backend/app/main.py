"""
OutreachX — FastAPI app (Phase 4 complete: AI + Email + Tracking + Database)
"""

import os, tempfile
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, RedirectResponse
from typing import Optional

from app.db.database            import create_tables
from app.api.routes.campaigns   import router as campaigns_router
from app.api.routes.tracking    import router as tracking_router
from app.agents.graph           import graph
from app.agents.tools.resume_parser import parse_resume
from app.services.email_sender  import send_email, send_campaign_emails
from app.services.tracker       import register_tracking, record_event, get_stats, get_all_events
from app.services.followup      import (start_scheduler, stop_scheduler,
                                        queue_followup, get_followup_queue, get_followup_stats)
from app.core.config            import get_settings

settings = get_settings()

PIXEL = bytes([
    0x47,0x49,0x46,0x38,0x39,0x61,0x01,0x00,0x01,0x00,0x80,0x00,0x00,
    0xff,0xff,0xff,0x00,0x00,0x00,0x21,0xf9,0x04,0x00,0x00,0x00,0x00,
    0x00,0x2c,0x00,0x00,0x00,0x00,0x01,0x00,0x01,0x00,0x00,0x02,0x02,
    0x44,0x01,0x00,0x3b
])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables on startup (Alembic handles migrations in prod)
    try:
        await create_tables()
        print("[DB] Tables ready")
    except Exception as e:
        print(f"[DB] Could not connect — running without DB: {e}")
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="OutreachX API",
    version="1.0.0",
    description="AI-powered B2B cold outreach — full pipeline",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://outreachx.vercel.app"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# Mount routers
app.include_router(campaigns_router)
app.include_router(tracking_router)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status":  "OutreachX API v1.0",
        "docs":    "/docs",
        "endpoints": {
            "AI pipeline":  "POST /agents/run",
            "Campaigns":    "GET/POST /campaigns",
            "Send emails":  "POST /campaigns/{id}/send",
            "Stats":        "GET /campaigns/{id}/stats",
            "Follow-ups":   "GET /followups/queue",
            "Tracking":     "GET /track/open/{id}",
            "Resume":       "POST /resume/parse",
        }
    }

@app.get("/health")
def health():
    return {"status": "ok"}


# ── Standalone AI pipeline (no DB) ───────────────────────────────────────────
# Keep this for quick testing without DB

@app.post("/agents/run")
async def run_agent(
    query:             Optional[str]        = Form(None),
    leads_file:        Optional[UploadFile] = File(None),
    sender_name:       str  = Form("Alex"),
    sender_value_prop: str  = Form("B2B SaaS growth and developer tooling"),
    target_role:       str  = Form("ceo"),
    resume_file:       Optional[UploadFile] = File(None),
):
    """Run full AI pipeline without saving to DB. Returns leads + emails directly."""
    tmp_leads = tmp_resume = None
    initial = {
        "errors": [], "leads": [],
        "sender_name": sender_name, "sender_value_prop": sender_value_prop,
        "sender_background": "", "target_role": target_role,
    }
    if leads_file:
        suffix = os.path.splitext(leads_file.filename)[-1].lower().lstrip(".")
        if suffix not in ("csv","xlsx","xls","json"):
            return JSONResponse(400, content={"error": f"Unsupported .{suffix}"})
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
            tmp.write(await leads_file.read()); tmp_leads = tmp.name
        initial.update({"uploaded_file_path": tmp_leads, "uploaded_file_type": suffix})
    elif query:
        initial["query"] = query.strip()
    else:
        return JSONResponse(status_code=400, content={"error": "Provide query or leads_file"})

    if resume_file:
        rsuffix = os.path.splitext(resume_file.filename)[-1].lower().lstrip(".")
        if rsuffix in ("pdf","txt"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{rsuffix}") as tmp:
                tmp.write(await resume_file.read()); tmp_resume = tmp.name
            profile = await parse_resume(tmp_resume, rsuffix)
            if profile.get("name"):
                initial["sender_name"] = profile["name"]
                initial["sender_background"] = profile.get("background_summary","")
                if profile.get("value_prop"): initial["sender_value_prop"] = profile["value_prop"]

    try:
        result = await graph.ainvoke(initial)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        for p in [tmp_leads, tmp_resume]:
            if p:
                try: os.unlink(p)
                except: pass

    leads  = result.get("enriched_leads") or result.get("leads",[])
    emails = result.get("validated_emails") or result.get("generated_emails",[])
    approved = sum(1 for e in emails if e.get("status")=="approved")

    return {
        "leads": leads, "emails": emails,
        "total": len(leads), "approved": approved,
        "current_step": result.get("current_step","Done"),
        "errors": result.get("errors",[]),
        "pipeline": {
            "discovered": len(result.get("leads",[])),
            "enriched":   len(leads),
            "emails_approved": approved,
        },
    }


# ── Email sending (standalone) ────────────────────────────────────────────────

@app.post("/emails/send")
async def send_single_email(
    to_email: str = Form(...), to_name: str = Form(""),
    subject: str = Form(...), body: str = Form(...),
    from_name: str = Form("OutreachX"), campaign_id: str = Form(""),
    lead_id: str = Form(""), dry_run: bool = Form(False),
    auto_followup: bool = Form(True), hook: str = Form(""), value_prop: str = Form(""),
):
    result = await send_email(
        to_email=to_email, to_name=to_name, subject=subject, body=body,
        from_name=from_name, campaign_id=campaign_id, lead_id=lead_id, dry_run=dry_run,
    )
    if result.get("success"):
        tid = result["tracking_id"]
        register_tracking(tid, campaign_id, lead_id, to_email)
        if auto_followup:
            queue_followup(
                tracking_id=tid, to_email=to_email, to_name=to_name, company=lead_id,
                original_subject=subject, hook=hook or body[:100],
                sender_name=from_name, value_prop=value_prop or "our services",
            )
            result["followup_queued"] = True
    return result


@app.get("/emails/stats")
def email_stats(campaign_id: Optional[str] = None):
    return get_stats(campaign_id)


# ── Follow-up management ──────────────────────────────────────────────────────

@app.get("/followups/queue")
def followup_queue():
    return {"queue": get_followup_queue(), "stats": get_followup_stats()}


@app.delete("/followups/{tracking_id}")
def cancel_followup(tracking_id: str):
    from app.services.followup import _followup_queue
    before = len(_followup_queue)
    _followup_queue[:] = [f for f in _followup_queue if f["tracking_id"] != tracking_id]
    return {"cancelled": before - len(_followup_queue) > 0}


# ── Resume parsing ────────────────────────────────────────────────────────────

@app.post("/resume/parse")
async def parse_resume_endpoint(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[-1].lower().lstrip(".")
    if suffix not in ("pdf","txt"):
        return JSONResponse(status_code=400, content={"error": "Upload PDF or TXT"})
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
        tmp.write(await file.read()); tmp_path = tmp.name
    try:
        return await parse_resume(tmp_path, suffix)
    finally:
        try: os.unlink(tmp_path)
        except: pass