import asyncio

import click

from async_scraper.scrapers import create_scraper


@click.command()
@click.argument("url")
def run_scraper(url):
    queue = asyncio.Queue()
    scraper = create_scraper(url, queue)
    asyncio.run(scraper.scrape(url))


if __name__ == "__main__":
    run_scraper()
