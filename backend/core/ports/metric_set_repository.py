from abc import ABC, abstractmethod
from typing import List, Optional

from ..domain.metric_set import MetricSet


class MetricSetRepository(ABC):
    @abstractmethod
    def list(self) -> List[MetricSet]:
        raise NotImplementedError

    @abstractmethod
    def get(self, metric_set_id: str) -> Optional[MetricSet]:
        raise NotImplementedError

    @abstractmethod
    def create(self, metric_set: MetricSet) -> MetricSet:
        raise NotImplementedError

    @abstractmethod
    def update(self, metric_set: MetricSet) -> MetricSet:
        raise NotImplementedError
