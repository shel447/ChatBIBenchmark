from abc import ABC, abstractmethod
from typing import List, Optional

from ..domain.schedule import ScheduleJob


class ScheduleRepository(ABC):
    @abstractmethod
    def create(self, schedule: ScheduleJob) -> ScheduleJob:
        raise NotImplementedError

    @abstractmethod
    def update(self, schedule: ScheduleJob) -> ScheduleJob:
        raise NotImplementedError

    @abstractmethod
    def delete(self, schedule_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def list(self, limit: int = 100) -> List[ScheduleJob]:
        raise NotImplementedError

    @abstractmethod
    def list_due(self, now_iso: str) -> List[ScheduleJob]:
        raise NotImplementedError

    @abstractmethod
    def get(self, schedule_id: str) -> Optional[ScheduleJob]:
        raise NotImplementedError

    @abstractmethod
    def get_active_for_task(self, task_id: str) -> Optional[ScheduleJob]:
        raise NotImplementedError
