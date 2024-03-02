import requests as r
import tiktoken
from openai import OpenAI
from env import EMBED_KEY, OPENAI_API_KEY, OPENAI_ORG_ID

OPENAI_SETTINGS = {"model": "text-embedding-3-large", "dimensions": 3072}
TABLE_NAME = "gpt4-discord-bot"

openai = OpenAI(api_key=OPENAI_API_KEY, organization=OPENAI_ORG_ID)
encoder = tiktoken.get_encoding("cl100k_base")

r.post(
    "https://embed-db.cyberthing.dev/api/table",
    json={"table_name": TABLE_NAME},
    headers={"Authorization": f"Bearer {EMBED_KEY}"},
)


def create_vectors(texts: list[str]) -> list[list[float]]:
    inputs = []
    count = 0
    for text in texts:
        tokens = encoder.encode(text, disallowed_special=())
        if count + len(tokens) >= 8192:
            break
        count += len(tokens)
        if text:
            inputs.append(text)
    responses = openai.embeddings.create(input=inputs, **OPENAI_SETTINGS).data
    return [response.embedding for response in responses]


def add_vectors(vectors: list[list[float]], texts: list[str]):
    # print(f"adding vectors {len(vectors)}")
    for vec, txt in zip(vectors, texts):
        r.post(
            "https://embed-db.cyberthing.dev/api/vector/add",
            json={"vector": vec, "text": txt, "table_name": TABLE_NAME},
            headers={"Authorization": f"Bearer {EMBED_KEY}"},
        )
    return


def query_vector(vector: list[float], n: int = 1) -> list[dict[str, str | float]]:
    response = r.post(
        "https://embed-db.cyberthing.dev/api/neighbors",
        json={"vector": vector, "n": n, "table_name": TABLE_NAME},
        headers={"Authorization": f"Bearer {EMBED_KEY}"},
    )
    return response.json()
