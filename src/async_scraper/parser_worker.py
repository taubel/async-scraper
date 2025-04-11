import asyncio
import logging

from .common.models import ParserItemModel
from .interfaces import ParserInterface
from .parser_database import JSONDatabase
from .scrapers.books_to_scrape.parsers import BookModel

logger = logging.getLogger(__name__)


class ParserWorker:
    def __init__(self, parser_queue: asyncio.Queue[ParserItemModel], database: JSONDatabase):
        self.parser_queue = parser_queue
        self.database = database

    async def run(self):
        while True:
            try:
                item = await self.parser_queue.get()
            except asyncio.QueueShutDown:
                logger.debug("ParserWorker shutting down")
                break
            url = item.url
            parser_class = item.parser
            contents = item.contents

            logger.debug("Parsing:")
            logger.debug(f"url: {url}")
            logger.debug(f"parser: {parser_class}")

            parser: ParserInterface = parser_class()
            # TODO type needs to be enforced
            parsed: BookModel = parser.parse(contents, url)
            self.parser_queue.task_done()

            await self.database.add(url, parsed.model_dump())
