import asyncio

from ..interfaces import ScraperInterface


class OxylabsSandboxScraper(ScraperInterface):
    # https://sandbox.oxylabs.io/products

    def __init__(self, parser_queue: asyncio.Queue):
        self.parser_queue = parser_queue
