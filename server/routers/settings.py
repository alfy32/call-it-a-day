from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Settings
from schemas import SettingsOut, SettingsIn
from datetime import date

router = APIRouter()

DEFAULTS = {
    "weekly_target_hours": "40",
    "daily_target_hours": "8",
    "tracking_start_date": str(date.today()),
}


def _get_all(db: Session) -> dict:
    rows = {s.key: s.value for s in db.query(Settings).all()}
    return {k: rows.get(k, v) for k, v in DEFAULTS.items()}


@router.get("/api/settings", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db)):
    cfg = _get_all(db)
    return SettingsOut(
        weekly_target_hours=float(cfg["weekly_target_hours"]),
        daily_target_hours=float(cfg["daily_target_hours"]),
        tracking_start_date=date.fromisoformat(cfg["tracking_start_date"]),
    )


@router.patch("/api/settings", response_model=SettingsOut)
def update_settings(patch: SettingsIn, db: Session = Depends(get_db)):
    def _set(key: str, value: str):
        row = db.query(Settings).filter(Settings.key == key).first()
        if row:
            row.value = value
        else:
            db.add(Settings(key=key, value=value))

    if patch.weekly_target_hours is not None:
        _set("weekly_target_hours", str(patch.weekly_target_hours))
    if patch.daily_target_hours is not None:
        _set("daily_target_hours", str(patch.daily_target_hours))
    if patch.tracking_start_date is not None:
        _set("tracking_start_date", str(patch.tracking_start_date))

    db.commit()
    return get_settings(db)
