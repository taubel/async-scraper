import asyncio
import logging

import click

from async_scraper.parser_worker import ParserWorker
from async_scraper.scrapers import create_scraper
from async_scraper.parser_database import JSONDatabase

logging.basicConfig(level=logging.DEBUG)


# TODO allow list of urls
@click.command()
@click.argument("url")
def run_scraper(url):
    queue = asyncio.Queue()
    scraper = create_scraper(url, queue)
    database = JSONDatabase("/tmp/data.json")
    parser_worker = ParserWorker(queue, database)

    async def worker():
        async with asyncio.TaskGroup() as tg:
            tg.create_task(scraper.scrape(url))
            tg.create_task(parser_worker.run())

    asyncio.run(worker())

    click.echo("Parsed data:")
    for url, data in database:
        click.echo("-" * 30)
        click.echo(url)
        click.echo(data)


if __name__ == "__main__":
    run_scraper()
