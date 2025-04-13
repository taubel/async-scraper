import asyncio
import logging
from concurrent.futures import ProcessPoolExecutor

from .common.models import ParserItemModel
from .interfaces import ParserInterface
from .parser_database import JSONDatabase
from .scrapers.books_to_scrape.parsers import BookModel

logger = logging.getLogger(__name__)


def parse(parser_queue: asyncio.Queue[ParserItemModel], database: JSONDatabase):
    while True:
        try:
            item = parser_queue.get_nowait()
        except (asyncio.QueueShutDown, asyncio.QueueEmpty):
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
        parser_queue.task_done()

        asyncio.run(database.add(url, parsed.model_dump()))


class ParserWorker:
    def __init__(self, parser_queue: asyncio.Queue[ParserItemModel], database: JSONDatabase):
        self.parser_queue = parser_queue
        self.database = database

    async def run(self):
        logger.debug("Running parse processes")
        with ProcessPoolExecutor() as executor:
            # TODO make process amount configurable
            for i in range(3):
                executor.submit(parse, self.parser_queue, self.database)
        logger.debug("Parse processes finished")
