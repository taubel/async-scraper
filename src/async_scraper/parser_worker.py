import asyncio
import logging

from .scrapers.books_to_scrape import ParserInterface

logger = logging.getLogger(__name__)


class ParserWorker:
    def __init__(self, parser_queue: asyncio.Queue):
        self.parser_queue = parser_queue

    async def run(self):
        while True:
            try:
                item = await self.parser_queue.get()
            except asyncio.QueueShutDown:
                logger.debug("ParserWorker shutting down")
                break
            url = item["url"]
            parser_class = item["parser"]
            contents = item["contents"]

            # TODO typehint item
            logger.debug("Parsing:")
            logger.debug(f"url: {url}")
            logger.debug(f"parser: {parser_class}")

            parser: ParserInterface = parser_class()
            parsed = parser.parse(contents, url)
            self.parser_queue.task_done()

            # TODO save to db
            print(parsed)
