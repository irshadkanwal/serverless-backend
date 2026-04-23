from abc import ABC, abstractmethod
from typing import TypeVar

from app.models.analyzer_model import AnalysisRequest

T = TypeVar("T")


class BaseAnalyzer[T](ABC):
    """Base class for all analyzers"""

    @abstractmethod
    async def analyze(self, request: AnalysisRequest) -> T:
        """Execute the analysis"""
