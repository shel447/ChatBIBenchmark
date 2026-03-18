from abc import ABC, abstractmethod
from typing import List, Optional

from ..domain.task import Task


class TaskRepository(ABC):
    @abstractmethod
    def create(self, task: Task) -> Task:
        raise NotImplementedError

    @abstractmethod
    def update(self, task: Task) -> Task:
        raise NotImplementedError

    @abstractmethod
    def list(self, limit: int = 50) -> List[Task]:
        raise NotImplementedError

    @abstractmethod
    def get(self, task_id: str) -> Optional[Task]:
        raise NotImplementedError
