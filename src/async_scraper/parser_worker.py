import asyncio
import logging
import queue
from concurrent.futures import ThreadPoolExecutor
from typing import Iterator

from .common.models import ParserItemModel
from .parser_database import JSONDatabase
from .scrapers.books_to_scrape.parsers import BasePageModel

logger = logging.getLogger(__name__)


def parse_item(item: ParserItemModel) -> BasePageModel:
    url = item.url
    parser_class = item.parser
    contents = item.contents

    logger.debug("Parsing:")
    logger.debug(f"url: {url}")
    logger.debug(f"parser: {parser_class}")

    parser = parser_class()
    parsed = parser.parse(contents, url)
    return parsed


def parse_queue(parser_queue) -> Iterator[BasePageModel]:
    while True:
        try:
            item: ParserItemModel = parser_queue.get_nowait()
        except queue.Empty:
            logger.debug("ParserWorker shutting down")
            break
        yield parse_item(item)


def run_parse_process(parser_queue, database: JSONDatabase):
    for item in parse_queue(parser_queue):
        asyncio.run(database.add(item.url, item.model_dump()))


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
                executor.submit(run_parse_process, self.parser_queue, self.database)
                for _ in range(self.worker_count)
            ]
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logger.exception(e)
        logger.debug("Parse processes finished")
