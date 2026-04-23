from abc import ABC, abstractmethod
from typing import TypeVar

T = TypeVar("T")
R = TypeVar("R")


class BaseAgent[T, R](ABC):
    @abstractmethod
    async def process(self, request: T) -> R:
        """Process the request and return response"""
