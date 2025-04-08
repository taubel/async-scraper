from abc import ABC, abstractmethod


class ScraperInterface(ABC):
    @abstractmethod
    def scrape(self, url: str):
        pass
