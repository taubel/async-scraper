from abc import ABC, abstractmethod


class ScraperInterface(ABC):
    @abstractmethod
    async def scrape(self, url: str):
        pass
