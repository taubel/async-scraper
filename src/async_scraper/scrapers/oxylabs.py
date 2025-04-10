import asyncio

from ..common.models import ParserItemModel
from ..interfaces import ScraperInterface


class OxylabsSandboxScraper(ScraperInterface):
    # https://sandbox.oxylabs.io/products

    def __init__(self, parser_queue: asyncio.Queue[ParserItemModel]):
        self.parser_queue = parser_queue

    async def scrape(self, url: str):
        raise NotImplementedError
