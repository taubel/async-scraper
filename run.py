import asyncio

from async_scraper.scraper import Scraper


def run_scraper():
    url = "https://books.toscrape.com/"

    scraper = Scraper()
    asyncio.run(scraper.scrape(url))


if __name__ == "__main__":
    run_scraper()
