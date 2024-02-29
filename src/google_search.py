from env import GOOGLE_API_KEY, GOOGLE_CSE_ID
import requests as r
from bs4 import BeautifulSoup


def do_page(url: str) -> list[str]:
    "Returns a list of paragraphs"
    page = r.get(url).text
    soup = BeautifulSoup(page, "html.parser")
    return [p.get_text().strip() for p in soup.find_all("p")]


def google_search(query: str) -> list[dict[str, str]]:
    results = r.get(
        f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}&gl=us&num=3"
    ).json()["items"]
    links = [result["link"] for result in results]
    return [{"link": link, "content": do_page(link)} for link in links]


if __name__ == "__main__":
    from json import dumps

    print(dumps(google_search("discord.py"), indent=2))

    tesla = do_page("https://en.wikipedia.org/wiki/Nikola_Tesla")
    print(tesla, len(tesla))
