import asyncio
import logging
import multiprocessing

import click

from async_scraper.parser_database import JSONDatabase
from async_scraper.parser_worker import ParserWorker
from async_scraper.scrapers import create_scraper

logging.basicConfig(level=logging.DEBUG)


# TODO allow list of urls
@click.command()
@click.argument("url")
def run_scraper(url):
    queue = multiprocessing.Queue()
    scraper = create_scraper(url, queue)
    database = JSONDatabase("/tmp/data.json")
    parser_worker = ParserWorker(queue, database)

    asyncio.run(scraper.scrape(url))
    # FIXME QueueFeederThread stays running
    parser_worker.run()

    click.echo("Parsed data:")
    for url, data in database:
        click.echo("-" * 30)
        click.echo(url)
        click.echo(data)


if __name__ == "__main__":
    run_scraper()
