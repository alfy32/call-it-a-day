from datetime import datetime, date, timedelta

ACTIVE_SESSION_CAP_HOURS = 12.0


def merge_intervals(
    intervals: list[tuple[datetime, datetime]],
) -> list[tuple[datetime, datetime]]:
    if not intervals:
        return []
    sorted_ivs = sorted(intervals, key=lambda x: x[0])
    result: list[list] = [list(sorted_ivs[0])]
    for start, end in sorted_ivs[1:]:
        if start <= result[-1][1]:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    return [(s, e) for s, e in result]


def manual_entry_hours(entry) -> float:
    if entry.start_at and entry.end_at:
        return (entry.end_at - entry.start_at).total_seconds() / 3600
    elif entry.hours is not None:
        return entry.hours
    return 0.0



def complete_sessions_hours(sessions: list, manual_entries: list, now: datetime) -> float:
    """Merged work hours from complete sessions (across computers) plus manual entries."""
    intervals = [
        (s.started_at, s.ended_at) for s in sessions if s.is_work
    ]
    merged = merge_intervals(intervals)
    total = sum((e - s).total_seconds() / 3600 for s, e in merged)
    total += sum(manual_entry_hours(m) for m in manual_entries)
    return total


def sessions_hours_in_window(
    complete_sessions: list,
    active_sessions: list,
    manual_entries: list,
    window_start: datetime,
    window_end: datetime,
    now: datetime,
) -> float:
    """Merged hours within [window_start, window_end), including active sessions."""
    clipped: list[tuple[datetime, datetime]] = []

    for s in complete_sessions:
        if not s.is_work:
            continue
        cs = max(s.started_at, window_start)
        ce = min(s.ended_at, window_end)
        if cs < ce:
            clipped.append((cs, ce))

    for s in active_sessions:
        if not s.is_work:
            continue
        raw_end = s.started_at + timedelta(hours=ACTIVE_SESSION_CAP_HOURS)
        effective_end = min(now, raw_end)
        cs = max(s.started_at, window_start)
        ce = min(effective_end, window_end)
        if cs < ce:
            clipped.append((cs, ce))

    merged = merge_intervals(clipped)
    total = sum((e - s).total_seconds() / 3600 for s, e in merged)
    total += sum(manual_entry_hours(m) for m in manual_entries)
    return total


def today_work_hours(
    complete_sessions: list,
    active_sessions: list,
    manual_entries: list,
    now: datetime,
) -> float:
    today = now.date()
    window_start = datetime.combine(today, datetime.min.time())
    window_end = now
    return sessions_hours_in_window(
        complete_sessions, active_sessions, manual_entries,
        window_start, window_end, now,
    )


def weekdays_elapsed(start: date, end: date) -> int:
    """Count Mon–Fri days from start up to but not including end."""
    count = 0
    current = start
    while current < end:
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)
    return count


def remaining_weekdays_in_week(today: date) -> int:
    """Count Mon–Fri days remaining in the week from today, inclusive."""
    dow = today.weekday()  # Mon=0 … Sat=5, Sun=6
    if dow == 6:  # Sunday — start of week, all 5 weekdays ahead
        return 5
    return max(0, 5 - dow)


def first_data_date(
    complete_sessions: list,
    active_sessions: list,
    all_manual: list,
    now: datetime,
) -> date | None:
    """Return the earliest date with any recorded data this calendar year."""
    year_start = date(now.year, 1, 1)
    candidates: list[date] = []
    for s in complete_sessions:
        d = s.started_at.date()
        if d >= year_start:
            candidates.append(d)
    for s in active_sessions:
        d = s.started_at.date()
        if d >= year_start:
            candidates.append(d)
    for m in all_manual:
        if m.date >= year_start:
            candidates.append(m.date)
    return min(candidates) if candidates else None


def calculate_hours_bank(
    complete_sessions: list,
    active_sessions: list,
    all_manual: list,
    daily_target: float,
    now: datetime,
) -> float:
    """
    Bank = total hours worked since the first day this year with data,
    minus weekdays elapsed × daily_target from that same start date.
    Sick days without a manual entry count against you.
    Returns 0.0 if there is no data yet this year.
    """
    start = first_data_date(complete_sessions, active_sessions, all_manual, now)
    if start is None:
        return 0.0
    expected = weekdays_elapsed(start, now.date() + timedelta(days=1)) * daily_target
    worked = sessions_hours_in_window(
        complete_sessions, active_sessions, all_manual,
        datetime.combine(start, datetime.min.time()),
        now, now,
    )
    return worked - expected


def calculate_stop_time(
    week_complete: list,
    week_active: list,
    week_manual: list,
    today_complete: list,
    today_active: list,
    today_manual: list,
    bank_at_week_start: float,
    weekly_target: float,
    now: datetime,
) -> datetime | None:
    today = now.date()

    if today.weekday() == 5:  # Saturday — end of week, no stop time
        return None

    adjusted_target = weekly_target - bank_at_week_start
    adjusted_target = max(0.0, min(adjusted_target, weekly_target * 1.5))

    pre_today_complete = [s for s in week_complete if s.started_at.date() < today]
    pre_today_active = [s for s in week_active if s.started_at.date() < today]
    pre_today_manual = [m for m in week_manual if m.date < today]
    hours_before_today = sessions_hours_in_window(
        pre_today_complete, pre_today_active, pre_today_manual,
        datetime.combine(today - timedelta(days=(today.weekday() + 1) % 7), datetime.min.time()),
        datetime.combine(today, datetime.min.time()),
        now,
    )

    remaining_days = remaining_weekdays_in_week(today) or 1
    hours_needed_today = (adjusted_target - hours_before_today) / remaining_days
    hours_today = today_work_hours(today_complete, today_active, today_manual, now)

    remaining = hours_needed_today - hours_today
    if remaining <= 0:
        return None

    return now + timedelta(hours=remaining)
