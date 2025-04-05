import asyncio

from async_scraper.scrapers import create_parser


def run_scraper():
    url = "https://books.toscrape.com/"

    scraper = create_parser(url)
    asyncio.run(scraper.scrape())


if __name__ == "__main__":
    run_scraper()
