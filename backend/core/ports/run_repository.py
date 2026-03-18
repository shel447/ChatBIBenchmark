from abc import ABC, abstractmethod
from typing import List, Optional

from ..domain.run import Run
from ..domain.run_case_result import RunCaseResult


class RunRepository(ABC):
    @abstractmethod
    def create(self, run: Run) -> Run:
        raise NotImplementedError

    @abstractmethod
    def update(self, run: Run) -> Run:
        raise NotImplementedError

    @abstractmethod
    def list(self, limit: int = 50) -> List[Run]:
        raise NotImplementedError

    @abstractmethod
    def list_by_task(self, task_id: str, limit: int = 50) -> List[Run]:
        raise NotImplementedError

    @abstractmethod
    def list_by_case_set(self, case_set_id: str, limit: int = 100) -> List[Run]:
        raise NotImplementedError

    @abstractmethod
    def get(self, run_id: str) -> Optional[Run]:
        raise NotImplementedError

    @abstractmethod
    def replace_case_results(self, run_id: str, results: List[RunCaseResult]) -> List[RunCaseResult]:
        raise NotImplementedError

    @abstractmethod
    def list_case_results(self, run_id: str) -> List[RunCaseResult]:
        raise NotImplementedError

    @abstractmethod
    def list_case_history(self, case_set_id: str, case_id: str, limit: int = 100) -> List[RunCaseResult]:
        raise NotImplementedError
