import asyncio

import click

from async_scraper.scrapers import create_parser


@click.command()
@click.argument("url")
def run_scraper(url):
    scraper = create_parser(url)
    asyncio.run(scraper.scrape(url))


if __name__ == "__main__":
    run_scraper()
