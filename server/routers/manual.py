from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import ManualEntry
from schemas import ManualEntryIn, ManualEntryOut
from calculations import manual_entry_hours

router = APIRouter()


def _to_out(m: ManualEntry) -> ManualEntryOut:
    return ManualEntryOut(
        id=m.id,
        date=m.date,
        start_at=m.start_at,
        end_at=m.end_at,
        hours=m.hours,
        hours_total=round(manual_entry_hours(m), 2),
        note=m.note,
    )


@router.get("/api/manual", response_model=list[ManualEntryOut])
def list_manual(for_date: date | None = None, db: Session = Depends(get_db)):
    q = db.query(ManualEntry)
    if for_date:
        q = q.filter(ManualEntry.date == for_date)
    return [_to_out(m) for m in q.order_by(ManualEntry.date.desc(), ManualEntry.id).all()]


@router.post("/api/manual", response_model=ManualEntryOut, status_code=201)
def create_manual(entry: ManualEntryIn, db: Session = Depends(get_db)):
    m = ManualEntry(
        date=entry.date,
        start_at=entry.start_at,
        end_at=entry.end_at,
        hours=entry.hours,
        note=entry.note,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return _to_out(m)


@router.delete("/api/manual/{entry_id}", status_code=204)
def delete_manual(entry_id: int, db: Session = Depends(get_db)):
    m = db.query(ManualEntry).filter(ManualEntry.id == entry_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Manual entry not found")
    db.delete(m)
    db.commit()
