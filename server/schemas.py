from datetime import datetime, date
from typing import Literal
from pydantic import BaseModel, Field, model_validator


# --- Sync ---

class SyncRequest(BaseModel):
    computer: str
    action: Literal["start", "end"]
    timestamp: datetime


class SyncResponse(BaseModel):
    status: Literal["created", "closed", "duplicate", "no_active_session"]


# --- Sessions ---

class ActiveSessionOut(BaseModel):
    id: int
    computer: str
    started_at: datetime
    duration_hours: float
    is_work: bool
    is_flagged_duration: bool
    is_flagged_duplicate: bool
    note: str | None = None

    model_config = {"from_attributes": True}


class PatchActiveSession(BaseModel):
    is_work: bool | None = None
    note: str | None = None


class CompleteSessionOut(BaseModel):
    id: int
    computer: str
    started_at: datetime
    ended_at: datetime
    duration_hours: float
    is_work: bool
    note: str | None = None

    model_config = {"from_attributes": True}


class PatchCompleteSession(BaseModel):
    is_work: bool | None = None
    note: str | None = None


class CompleteSessionIn(BaseModel):
    computer: str
    started_at: datetime
    ended_at: datetime
    is_work: bool = True
    note: str | None = None


# --- Manual Entries ---

class ManualEntryOut(BaseModel):
    id: int
    date: date
    start_at: datetime | None
    end_at: datetime | None
    hours: float | None
    hours_total: float
    note: str | None = None

    model_config = {"from_attributes": True}


class ManualEntryIn(BaseModel):
    date: date
    start_at: datetime | None = None
    end_at: datetime | None = None
    hours: float | None = Field(None, gt=0, le=24)
    note: str | None = None

    @model_validator(mode="after")
    def check_valid_form(self):
        has_range = self.start_at is not None and self.end_at is not None
        has_start_only = self.start_at is not None and self.hours is not None and self.end_at is None
        has_hours_only = self.hours is not None and self.start_at is None

        if not (has_range or has_start_only or has_hours_only):
            raise ValueError(
                "Manual entry must be: full range (start_at + end_at), "
                "start only (start_at + hours), or hours only (hours alone)"
            )
        if has_range and self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


# --- Summary ---

class TodaySummary(BaseModel):
    date: date
    hours_worked: float
    hours_remaining: float
    daily_target: float
    is_done: bool
    stop_time: datetime | None
    bank_hours: float
    active_sessions: list[ActiveSessionOut]
    complete_sessions: list[CompleteSessionOut]
    manual_entries: list[ManualEntryOut]


class DayBreakdown(BaseModel):
    date: date
    hours: float
    is_today: bool


class WeekSummary(BaseModel):
    week_start: date
    total_hours: float
    weekly_target: float
    adjusted_target: float
    hours_remaining: float
    remaining_weekdays: int
    daily_breakdown: list[DayBreakdown]


class DayStats(BaseModel):
    date: date
    hours: float
    session_count: int
    is_flagged: bool = False


class DailySummary(BaseModel):
    days: list[DayStats]


class WeekStats(BaseModel):
    week_start: date
    total_hours: float
    avg_hours_per_day: float
    delta_from_40: float


class WeeklySummary(BaseModel):
    weeks: list[WeekStats]


# --- Settings ---

class SettingsOut(BaseModel):
    weekly_target_hours: float
    daily_target_hours: float
    tracking_start_date: date


class SettingsIn(BaseModel):
    weekly_target_hours: float | None = None
    daily_target_hours: float | None = None
    tracking_start_date: date | None = None


# --- Week detail ---

class DayDetail(BaseModel):
    date: date
    hours: float
    is_today: bool
    active_sessions: list[ActiveSessionOut]
    complete_sessions: list[CompleteSessionOut]
    manual_entries: list[ManualEntryOut]


class WeekDetail(BaseModel):
    week_start: date
    days: list[DayDetail]


# --- Sessions list ---

class SessionsResponse(BaseModel):
    sessions: list[CompleteSessionOut]
    total: int
    page: int
    per_page: int
