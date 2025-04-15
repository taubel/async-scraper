from abc import ABC, abstractmethod


class ParserInterface(ABC):
    @classmethod
    @abstractmethod
    # TODO use BasePageModel here
    def parse(cls, contents: str, url: str) -> dict:
        pass
