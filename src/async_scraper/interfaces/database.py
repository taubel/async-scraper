from abc import ABC, abstractmethod
from typing import Any


class AsyncDatabaseInterface(ABC):
    @abstractmethod
    async def add(self, url: str, value: Any):
        pass

    @abstractmethod
    async def get(self, url: str) -> Any:
        pass

