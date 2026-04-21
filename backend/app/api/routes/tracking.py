"""Tracking routes — wire DB updates to open/click/reply events."""

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.crud     import mark_email_opened, mark_email_clicked, mark_email_replied
from app.services.tracker import record_event

router = APIRouter(prefix="/track", tags=["tracking"])

PIXEL = bytes([
    0x47,0x49,0x46,0x38,0x39,0x61,0x01,0x00,0x01,0x00,0x80,0x00,0x00,
    0xff,0xff,0xff,0x00,0x00,0x00,0x21,0xf9,0x04,0x00,0x00,0x00,0x00,
    0x00,0x2c,0x00,0x00,0x00,0x00,0x01,0x00,0x01,0x00,0x00,0x02,0x02,
    0x44,0x01,0x00,0x3b
])


@router.get("/open/{tracking_id}")
async def track_open(tracking_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    record_event(tracking_id, "open")
    await mark_email_opened(db, tracking_id)
    return Response(content=PIXEL, media_type="image/gif",
                    headers={"Cache-Control": "no-store"})


@router.get("/click/{tracking_id}")
async def track_click(tracking_id: str, url: str = "", db: AsyncSession = Depends(get_db)):
    record_event(tracking_id, "click", {"url": url})
    await mark_email_clicked(db, tracking_id)
    return RedirectResponse(url=url, status_code=302) if url else {"tracked": True}


@router.post("/reply/{tracking_id}")
async def track_reply(tracking_id: str, db: AsyncSession = Depends(get_db)):
    record_event(tracking_id, "reply")
    await mark_email_replied(db, tracking_id)
    return {"tracked": True}


@router.get("/unsubscribe/{tracking_id}")
async def track_unsubscribe(tracking_id: str, db: AsyncSession = Depends(get_db)):
    record_event(tracking_id, "unsubscribe")
    return {"message": "You have been unsubscribed."}