from abc import ABC, abstractmethod
from typing import List, Optional

from ..domain.run import Run


class RunRepository(ABC):
    @abstractmethod
    def create(self, run: Run) -> Run:
        raise NotImplementedError

    @abstractmethod
    def list(self, limit: int = 50) -> List[Run]:
        raise NotImplementedError

    @abstractmethod
    def get(self, run_id: str) -> Optional[Run]:
        raise NotImplementedError
