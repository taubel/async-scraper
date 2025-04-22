import asyncio
import logging
import multiprocessing

import click

from async_scraper.databases import JSONDatabase
from async_scraper.parser_worker import ParserWorker
from async_scraper.scrapers import create_scraper

logging.basicConfig(level=logging.DEBUG)


# TODO allow list of urls
@click.command()
@click.argument("url")
def run_scraper(url):
    queue = multiprocessing.Queue()
    scraper = create_scraper(url, queue)
    lock = multiprocessing.Lock()
    database = JSONDatabase("/tmp/data.json", lock)
    parser_worker = ParserWorker(queue, database)

    asyncio.run(scraper.scrape(url))
    parser_worker.run()

    click.echo("Parsed data:")
    for url, data in database:
        click.echo("-" * 30)
        click.echo(url)
        click.echo(data)


if __name__ == "__main__":
    run_scraper()
