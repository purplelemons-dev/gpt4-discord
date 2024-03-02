from env import GOOGLE_API_KEY, GOOGLE_CSE_ID
import requests as r
from bs4 import BeautifulSoup
from vectors import add_vectors, query_vector, create_vectors
from threading import Thread


def do_page(url: str) -> list[str]:
    "Returns a list of paragraphs"
    page = r.get(url).text
    soup = BeautifulSoup(page, "html.parser")
    return [
        p.get_text().strip().replace("\n", " ").replace("  ", " ")
        for p in soup.find_all("p")
    ]


def google_search(query: str) -> list[dict[str, str]]:
    results = r.get(
        f"https://www.googleapis.com/customsearch/v1?"
        f"q={query}&"
        f"key={GOOGLE_API_KEY}&"
        f"cx={GOOGLE_CSE_ID}&"
        "gl=us&num=3"
    ).json()["items"]
    links: list[str] = [result["link"] for result in results]

    contents = []

    def append_content(link: str):
        contents.append({"link": link, "content": do_page(link)})

    threads = [Thread(target=append_content, args=(link,)) for link in links]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return contents


def turbo_search(query: str) -> list[str]:
    results = google_search(query)
    texts: list[list[str]] = [result["content"] for result in results]
    threads: list[Thread] = []

    for vectors, record in [(create_vectors(texts=record), record) for record in texts]:
        t = Thread(target=add_vectors, args=(vectors, record))
        t.start()
        threads.append(t)

    query_vec = create_vectors(texts=[query])[0]
    for t in threads:
        t.join()
    response = query_vector(query_vec, n=4)

    return [i["text"] for i in response]


if __name__ == "__main__":
    from json import dumps
    from time import perf_counter

    # print(dumps(google_search("discord.py"), indent=2))

    # tesla = do_page("https://en.wikipedia.org/wiki/Nikola_Tesla")
    # print(f"{len(tesla)= }")
    st = perf_counter()
    turbo_tesla = turbo_search("technology trends in 2024")
    print(turbo_tesla)
    et = perf_counter()
    print(f"{et-st= }")
