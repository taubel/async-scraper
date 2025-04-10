from abc import ABC, abstractmethod


class ParserInterface(ABC):
    @classmethod
    @abstractmethod
    def parse(cls, contents: str, url: str) -> dict:
        pass
