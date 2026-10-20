"""Retrieval + generation."""
from dataclasses import dataclass

import numpy as np
import psycopg
from openai import OpenAI
from pgvector.psycopg import register_vector

from config import CHAT_MODEL, DATABASE_URL, EMBED_MODEL, TOP_K

SYSTEM_PROMPT = """You are the customer assistant for Nimbus Coffee Co.
Answer the question using ONLY the context below. Be concise and specific.
If the context does not contain the answer, say "I don't know based on the Nimbus documents."
"""

_client = OpenAI()


@dataclass
class Retrieved:
    source: str
    content: str
    distance: float


@dataclass
class RagAnswer:
    answer: str
    contexts: list[Retrieved]


def embed(text: str) -> np.ndarray:
    resp = _client.embeddings.create(model=EMBED_MODEL, input=text)
    return np.array(resp.data[0].embedding)


def retrieve(question: str, k: int = TOP_K) -> list[Retrieved]:
    query_vec = embed(question)
    with psycopg.connect(DATABASE_URL) as conn:
        register_vector(conn)
        rows = conn.execute(
            """
            SELECT source, content, embedding <=> %s AS distance
            FROM chunks
            ORDER BY embedding <=> %s
            LIMIT %s
            """,
            (query_vec, query_vec, k),
        ).fetchall()
    return [Retrieved(source=r[0], content=r[1], distance=float(r[2])) for r in rows]


def answer(question: str, k: int = TOP_K) -> RagAnswer:
    contexts = retrieve(question, k)
    context_block = "\n\n---\n\n".join(c.content for c in contexts)
    resp = _client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context_block}\n\nQuestion: {question}"},
        ],
    )
    return RagAnswer(answer=resp.choices[0].message.content.strip(), contexts=contexts)
