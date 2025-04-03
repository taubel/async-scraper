import aiohttp


async def get_page_contents(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            # TODO check status
            return await resp.text()


class Scraper:
    async def scrape(self, url: str):
        contents = await get_page_contents(url)
        print(contents)
