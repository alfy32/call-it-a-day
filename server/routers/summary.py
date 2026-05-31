from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import ActiveSession, CompleteSession, ManualEntry, Settings
from schemas import (
    TodaySummary, WeekSummary, DailySummary, WeeklySummary,
    DayBreakdown, DayStats, WeekStats,
    ActiveSessionOut, CompleteSessionOut, ManualEntryOut,
    DayDetail, WeekDetail,
)
from calculations import (
    sessions_hours_in_window, today_work_hours,
    calculate_stop_time, weekdays_elapsed, remaining_weekdays_in_week,
    active_session_effective_hours, manual_entry_hours, ACTIVE_SESSION_CAP_HOURS,
)

router = APIRouter()


def _get_cfg(db: Session) -> dict:
    rows = {s.key: s.value for s in db.query(Settings).all()}
    if "tracking_start_date" in rows:
        tracking_start = date.fromisoformat(rows["tracking_start_date"])
    else:
        first = db.query(CompleteSession).order_by(CompleteSession.started_at).first()
        tracking_start = first.started_at.date() if first else date.today()
    return {
        "weekly_target": float(rows.get("weekly_target_hours", "40")),
        "daily_target": float(rows.get("daily_target_hours", "8")),
        "tracking_start": tracking_start,
    }


def _active_session_out(session: ActiveSession, now: datetime, computers_with_multiple: set) -> ActiveSessionOut:
    raw_hours = (now - session.started_at).total_seconds() / 3600
    is_dur_flagged = raw_hours > ACTIVE_SESSION_CAP_HOURS
    return ActiveSessionOut(
        id=session.id,
        computer=session.computer,
        started_at=session.started_at,
        duration_hours=round(min(raw_hours, ACTIVE_SESSION_CAP_HOURS), 2),
        is_flagged_duration=is_dur_flagged,
        is_flagged_duplicate=session.computer in computers_with_multiple,
        note=session.note,
    )


def _complete_session_out(session: CompleteSession) -> CompleteSessionOut:
    dur = (session.ended_at - session.started_at).total_seconds() / 3600
    return CompleteSessionOut(
        id=session.id,
        computer=session.computer,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_hours=round(dur, 2),
        is_work=session.is_work,
        note=session.note,
    )


def _manual_entry_out(entry: ManualEntry) -> ManualEntryOut:
    return ManualEntryOut(
        id=entry.id,
        date=entry.date,
        start_at=entry.start_at,
        end_at=entry.end_at,
        hours=entry.hours,
        hours_total=round(manual_entry_hours(entry), 2),
        note=entry.note,
    )


def _flagged_computers(active_sessions: list[ActiveSession]) -> set:
    from collections import Counter
    counts = Counter(s.computer for s in active_sessions)
    return {c for c, n in counts.items() if n > 1}


@router.get("/api/summary/today", response_model=TodaySummary)
def summary_today(db: Session = Depends(get_db)):
    now = datetime.now()
    today = now.date()
    cfg = _get_cfg(db)

    today_start = datetime.combine(today, datetime.min.time())

    active = db.query(ActiveSession).all()
    today_complete = (
        db.query(CompleteSession)
        .filter(CompleteSession.started_at >= today_start)
        .order_by(CompleteSession.started_at)
        .all()
    )
    today_manual = (
        db.query(ManualEntry)
        .filter(ManualEntry.date == today)
        .all()
    )

    flagged = _flagged_computers(active)
    hours_worked = today_work_hours(today_complete, active, today_manual, now)
    daily_target = cfg["daily_target"]
    is_done = hours_worked >= daily_target

    # Bank at start of this week
    week_start = today - timedelta(days=(today.weekday() + 1) % 7)
    week_start_dt = datetime.combine(week_start, datetime.min.time())
    pre_week_complete = (
        db.query(CompleteSession)
        .filter(CompleteSession.started_at < week_start_dt)
        .all()
    )
    pre_week_manual = (
        db.query(ManualEntry)
        .filter(ManualEntry.date < week_start)
        .all()
    )
    # No active sessions before this week
    pre_week_hours = sessions_hours_in_window(
        pre_week_complete, [], pre_week_manual,
        datetime.combine(cfg["tracking_start"], datetime.min.time()),
        week_start_dt,
        now,
    )
    expected_before_week = weekdays_elapsed(cfg["tracking_start"], week_start) * cfg["daily_target"]
    bank_at_week_start = pre_week_hours - expected_before_week

    week_complete = (
        db.query(CompleteSession)
        .filter(CompleteSession.started_at >= week_start_dt)
        .all()
    )
    week_manual = (
        db.query(ManualEntry)
        .filter(ManualEntry.date >= week_start, ManualEntry.date <= today)
        .all()
    )

    # Running bank across all time
    all_complete = db.query(CompleteSession).all()
    all_manual_ever = db.query(ManualEntry).all()
    all_worked = sessions_hours_in_window(
        all_complete, active, all_manual_ever,
        datetime.combine(cfg["tracking_start"], datetime.min.time()),
        now, now,
    )
    expected_total = weekdays_elapsed(cfg["tracking_start"], today + timedelta(days=1)) * cfg["daily_target"]
    bank_hours = round(all_worked - expected_total, 2)

    stop_time = calculate_stop_time(
        week_complete=week_complete,
        week_active=active,
        week_manual=week_manual,
        today_complete=today_complete,
        today_active=active,
        today_manual=today_manual,
        bank_at_week_start=bank_at_week_start,
        weekly_target=cfg["weekly_target"],
        now=now,
    )

    hours_remaining = round((stop_time - now).total_seconds() / 3600, 2) if stop_time else 0.0

    return TodaySummary(
        date=today,
        hours_worked=round(hours_worked, 2),
        hours_remaining=hours_remaining,
        daily_target=daily_target,
        is_done=is_done,
        stop_time=stop_time,
        bank_hours=bank_hours,
        active_sessions=[_active_session_out(s, now, flagged) for s in active],
        complete_sessions=[_complete_session_out(s) for s in today_complete],
        manual_entries=[_manual_entry_out(m) for m in today_manual],
    )


@router.get("/api/summary/week", response_model=WeekSummary)
def summary_week(db: Session = Depends(get_db)):
    now = datetime.now()
    today = now.date()
    cfg = _get_cfg(db)
    week_start = today - timedelta(days=(today.weekday() + 1) % 7)
    week_start_dt = datetime.combine(week_start, datetime.min.time())

    active = db.query(ActiveSession).all()

    pre_week_complete = (
        db.query(CompleteSession)
        .filter(CompleteSession.started_at < week_start_dt)
        .all()
    )
    pre_week_manual = db.query(ManualEntry).filter(ManualEntry.date < week_start).all()
    pre_week_hours = sessions_hours_in_window(
        pre_week_complete, [], pre_week_manual,
        datetime.combine(cfg["tracking_start"], datetime.min.time()),
        week_start_dt, now,
    )
    expected_before_week = weekdays_elapsed(cfg["tracking_start"], week_start) * cfg["daily_target"]
    bank_at_week_start = pre_week_hours - expected_before_week

    adjusted_target = max(0.0, min(cfg["weekly_target"] - bank_at_week_start, cfg["weekly_target"] * 1.5))

    breakdown = []
    total_hours = 0.0
    for i in range(7):
        d = week_start + timedelta(days=i)
        if d > today:
            break
        d_start = datetime.combine(d, datetime.min.time())
        d_end = datetime.combine(d + timedelta(days=1), datetime.min.time())
        cutoff = now if d == today else d_end
        d_complete = (
            db.query(CompleteSession)
            .filter(CompleteSession.started_at >= d_start, CompleteSession.started_at < d_end)
            .all()
        )
        d_active = active if d == today else []
        d_manual = db.query(ManualEntry).filter(ManualEntry.date == d).all()
        hours = sessions_hours_in_window(d_complete, d_active, d_manual, d_start, cutoff, now)
        total_hours += hours
        breakdown.append(DayBreakdown(date=d, hours=round(hours, 2), is_today=(d == today)))

    hours_remaining = max(0.0, round(adjusted_target - total_hours, 2))

    return WeekSummary(
        week_start=week_start,
        total_hours=round(total_hours, 2),
        weekly_target=cfg["weekly_target"],
        adjusted_target=round(adjusted_target, 2),
        hours_remaining=hours_remaining,
        remaining_weekdays=remaining_weekdays_in_week(today),
        daily_breakdown=breakdown,
    )


@router.get("/api/summary/daily", response_model=DailySummary)
def summary_daily(days: int = 60, db: Session = Depends(get_db)):
    now = datetime.now()
    today = now.date()
    active = db.query(ActiveSession).all()
    result = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        d_start = datetime.combine(d, datetime.min.time())
        d_end = datetime.combine(d + timedelta(days=1), datetime.min.time())
        cutoff = now if d == today else d_end
        d_complete = (
            db.query(CompleteSession)
            .filter(CompleteSession.started_at >= d_start, CompleteSession.started_at < d_end)
            .all()
        )
        d_active = active if d == today else []
        d_manual = db.query(ManualEntry).filter(ManualEntry.date == d).all()
        hours = sessions_hours_in_window(d_complete, d_active, d_manual, d_start, cutoff, now)
        session_count = len(d_complete) + (len(d_active) if d == today else 0)
        result.append(DayStats(date=d, hours=round(hours, 2), session_count=session_count))
    return DailySummary(days=result)


@router.get("/api/summary/weekly", response_model=WeeklySummary)
def summary_weekly(weeks: int = 26, db: Session = Depends(get_db)):
    now = datetime.now()
    today = now.date()
    week_start = today - timedelta(days=(today.weekday() + 1) % 7)
    active = db.query(ActiveSession).all()
    result = []
    for i in range(weeks - 1, -1, -1):
        ws = week_start - timedelta(weeks=i)
        we = ws + timedelta(days=6)
        ws_dt = datetime.combine(ws, datetime.min.time())
        we_dt = datetime.combine(we + timedelta(days=1), datetime.min.time())
        cap = now if we >= today else we_dt
        w_active = active if we >= today else []
        w_complete = (
            db.query(CompleteSession)
            .filter(CompleteSession.started_at >= ws_dt, CompleteSession.started_at < we_dt)
            .all()
        )
        w_manual = (
            db.query(ManualEntry)
            .filter(ManualEntry.date >= ws, ManualEntry.date <= min(we, today))
            .all()
        )
        total = sessions_hours_in_window(w_complete, w_active, w_manual, ws_dt, cap, now)
        worked_days = weekdays_elapsed(ws, min(we + timedelta(days=1), today + timedelta(days=1)))
        avg = round(total / worked_days, 2) if worked_days else 0.0
        result.append(WeekStats(
            week_start=ws,
            total_hours=round(total, 2),
            avg_hours_per_day=avg,
            delta_from_40=round(total - 40.0, 2),
        ))
    return WeeklySummary(weeks=result)


@router.get("/api/summary/week/{week_start_str}", response_model=WeekDetail)
def summary_week_detail(week_start_str: str, db: Session = Depends(get_db)):
    from datetime import date as date_type
    week_start = date_type.fromisoformat(week_start_str)
    now = datetime.now()
    today = now.date()
    active = db.query(ActiveSession).all()
    flagged = _flagged_computers(active)

    days = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        if d > today:
            break
        is_today = d == today
        d_start = datetime.combine(d, datetime.min.time())
        d_end = datetime.combine(d + timedelta(days=1), datetime.min.time())
        cutoff = now if is_today else d_end
        d_complete = (
            db.query(CompleteSession)
            .filter(CompleteSession.started_at >= d_start, CompleteSession.started_at < d_end)
            .order_by(CompleteSession.started_at)
            .all()
        )
        d_active = active if is_today else []
        d_manual = db.query(ManualEntry).filter(ManualEntry.date == d).all()
        hours = sessions_hours_in_window(d_complete, d_active, d_manual, d_start, cutoff, now)
        days.append(DayDetail(
            date=d,
            hours=round(hours, 2),
            is_today=is_today,
            active_sessions=[_active_session_out(s, now, flagged) for s in d_active],
            complete_sessions=[_complete_session_out(s) for s in d_complete],
            manual_entries=[_manual_entry_out(m) for m in d_manual],
        ))

    return WeekDetail(week_start=week_start, days=days)
