import asyncio
import logging
import queue
from concurrent.futures import ProcessPoolExecutor, wait

from .interfaces import ParserInterface
from .parser_database import JSONDatabase
from .scrapers.books_to_scrape.parsers import BasePageModel

logger = logging.getLogger(__name__)


def parse(parser_queue, database: JSONDatabase):
    while True:
        try:
            item = parser_queue.get_nowait()
        except queue.Empty:
            logger.debug("ParserWorker shutting down")
            break
        url = item.url
        parser_class = item.parser
        contents = item.contents

        logger.debug("Parsing:")
        logger.debug(f"url: {url}")
        logger.debug(f"parser: {parser_class}")

        parser: ParserInterface = parser_class()
        parsed: BasePageModel = parser.parse(contents, url)

        asyncio.run(database.add(url, parsed.model_dump()))


class ParserWorker:
    def __init__(self, parser_queue, database: JSONDatabase):
        self.parser_queue = parser_queue
        self.database = database

    def run(self):
        logger.debug("Running parse processes")
        with ProcessPoolExecutor() as executor:
            # TODO using executor does not work
            # TODO make process amount configurable
            futures = [
                executor.submit(parse, self.parser_queue, self.database) for _ in range(3)
            ]
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logger.exception(e)
        logger.debug("Parse processes finished")
