import asyncio
import logging
import queue
from concurrent.futures import ThreadPoolExecutor

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
    def __init__(self, parser_queue, database: JSONDatabase, worker_count: int = 3):
        self.parser_queue = parser_queue
        self.database = database
        self.worker_count = worker_count

    def run(self):
        logger.debug("Running parse processes")
        # FIXME this would benefit from splitting parsing into multiple processes instead of threads
        #  but parser_queue and database were not designed as pickleable.
        #  Either refactor existing classes, or separate scraping and parsing into different processes
        #  and implement IPC using atomic databases
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(parse, self.parser_queue, self.database)
                for _ in range(self.worker_count)
            ]
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logger.exception(e)
        logger.debug("Parse processes finished")
