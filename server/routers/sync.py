from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import ActiveSession, CompleteSession
from schemas import SyncRequest, SyncResponse

router = APIRouter()


@router.post("/api/sync", response_model=SyncResponse)
def sync(request: SyncRequest, db: Session = Depends(get_db)):
    if request.action == "start":
        existing = (
            db.query(ActiveSession)
            .filter(ActiveSession.computer == request.computer)
            .filter(ActiveSession.started_at == request.timestamp)
            .first()
        )
        if existing:
            return SyncResponse(status="duplicate")

        db.add(ActiveSession(
            computer=request.computer,
            started_at=request.timestamp,
        ))
        db.commit()
        return SyncResponse(status="created")

    else:  # end
        active = (
            db.query(ActiveSession)
            .filter(ActiveSession.computer == request.computer)
            .order_by(ActiveSession.started_at.desc())
            .first()
        )
        if not active:
            return SyncResponse(status="no_active_session")

        db.add(CompleteSession(
            computer=active.computer,
            started_at=active.started_at,
            ended_at=request.timestamp,
            is_work=active.is_work,
            note=active.note,
        ))
        db.delete(active)
        db.commit()
        return SyncResponse(status="closed")
