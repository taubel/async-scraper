import asyncio

from async_scraper.scrapers import BooksToScrapeScraper


def run_scraper():
    url = "https://books.toscrape.com/"

    scraper = BooksToScrapeScraper(url)
    asyncio.run(scraper.scrape())


if __name__ == "__main__":
    run_scraper()
