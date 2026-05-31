from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import ActiveSession, CompleteSession
from schemas import SessionsResponse, CompleteSessionOut, PatchCompleteSession, PatchActiveSession

router = APIRouter()


def _to_out(s: CompleteSession) -> CompleteSessionOut:
    dur = (s.ended_at - s.started_at).total_seconds() / 3600
    return CompleteSessionOut(
        id=s.id,
        computer=s.computer,
        started_at=s.started_at,
        ended_at=s.ended_at,
        duration_hours=round(dur, 2),
        is_work=s.is_work,
        note=s.note,
    )


@router.get("/api/sessions", response_model=SessionsResponse)
def list_sessions(page: int = 1, per_page: int = 50, db: Session = Depends(get_db)):
    total = db.query(CompleteSession).count()
    sessions = (
        db.query(CompleteSession)
        .order_by(CompleteSession.started_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return SessionsResponse(
        sessions=[_to_out(s) for s in sessions],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.patch("/api/sessions/{session_id}", response_model=CompleteSessionOut)
def patch_session(session_id: int, patch: PatchCompleteSession, db: Session = Depends(get_db)):
    session = db.query(CompleteSession).filter(CompleteSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if patch.is_work is not None:
        session.is_work = patch.is_work
    if patch.note is not None:
        session.note = patch.note
    db.commit()
    db.refresh(session)
    return _to_out(session)


@router.delete("/api/sessions/{session_id}", status_code=204)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(CompleteSession).filter(CompleteSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()


@router.patch("/api/active_sessions/{session_id}", status_code=204)
def patch_active_session(session_id: int, patch: PatchActiveSession, db: Session = Depends(get_db)):
    session = db.query(ActiveSession).filter(ActiveSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")
    if patch.is_work is not None:
        session.is_work = patch.is_work
    if patch.note is not None:
        session.note = patch.note
    db.commit()


@router.delete("/api/active_sessions/{session_id}", status_code=204)
def dismiss_active_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ActiveSession).filter(ActiveSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")
    db.delete(session)
    db.commit()
