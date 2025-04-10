import asyncio
import logging

import click

from async_scraper.parser_worker import ParserWorker
from async_scraper.scrapers import create_scraper

logging.basicConfig(level=logging.DEBUG)


# TODO allow list of urls
@click.command()
@click.argument("url")
def run_scraper(url):
    queue = asyncio.Queue()
    scraper = create_scraper(url, queue)
    parser_worker = ParserWorker(queue)

    async def worker():
        async with asyncio.TaskGroup() as tg:
            tg.create_task(scraper.scrape(url))
            tg.create_task(parser_worker.run())

    asyncio.run(worker())


if __name__ == "__main__":
    run_scraper()
