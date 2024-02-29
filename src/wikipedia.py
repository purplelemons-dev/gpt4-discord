import requests as r
from typing import Union, Literal


def wiki_titles(
    query: str,
) -> list[Union[dict[Literal["pageid"], int], dict[Literal["title"], str]]]:
    pages = r.get("https://wiki-api.purplelemons.dev/api/titles?q=" + query).json()[
        "pages"
    ]
    return [{"pageid": page["pageid"], "title": page["title"]} for page in pages]


def wiki_content(pageid: int) -> str:
    return (
        r.get("https://wiki-api.purplelemons.dev/api/page?pageid=" + str(pageid))
        .json()["extract"]
        .replace("\n", " ")
    )
