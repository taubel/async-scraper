import asyncio
import re

from .books_to_scrape import BooksToScrapeScraper
from .oxylabs import OxylabsSandboxScraper
from ..interfaces import ScraperInterface


# TODO typehint item type
def create_scraper(url: str, parser_queue: asyncio.Queue) -> ScraperInterface:
    if re.match(r"^https?://books.toscrape.com.*$", url):
        return BooksToScrapeScraper(parser_queue)
    elif re.match(r"^https?://sandbox.oxylabs.io/products.*$", url):
        return OxylabsSandboxScraper(parser_queue)
    else:
        raise ValueError(f"No scraper defined for url: {url}")
