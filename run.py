import asyncio

from async_scraper.scraper import Scraper, Scrapeables


def run_scraper():
    url = "https://books.toscrape.com/"

    scraper = Scraper(url)
    asyncio.run(scraper.scrape(Scrapeables.book))


if __name__ == "__main__":
    run_scraper()
