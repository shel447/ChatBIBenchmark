from dataclasses import dataclass
from typing import Optional


@dataclass
class ScheduleJob:
    schedule_id: str
    name: str
    task_id: str
    schedule_type: str
    run_at: Optional[str]
    daily_time: Optional[str]
    timezone: str
    schedule_status: str
    last_triggered_at: Optional[str]
    next_triggered_at: Optional[str]
    created_at: str
    updated_at: str
