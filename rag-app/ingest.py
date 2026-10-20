"""Chunk the Markdown docs in data/, embed them with OpenAI, and store them in pgvector."""
from pathlib import Path

import psycopg
from openai import OpenAI
from pgvector.psycopg import register_vector

from config import DATABASE_URL, EMBED_MODEL

DATA_DIR = Path(__file__).parent / "data"
SCHEMA = (Path(__file__).parent / "db" / "init.sql").read_text()
MAX_CHARS = 500


def chunk_markdown(text: str) -> list[str]:
    """Split on blank lines, then pack paragraphs into chunks of up to MAX_CHARS.

    Each chunk is prefixed with the document title so it stays meaningful on its own.
    """
    lines = text.strip().splitlines()
    title = lines[0].lstrip("# ").strip()
    paragraphs = [p.strip() for p in "\n".join(lines[1:]).split("\n\n") if p.strip()]

    chunks, current = [], ""
    for para in paragraphs:
        if current and len(current) + len(para) > MAX_CHARS:
            chunks.append(current)
            current = ""
        current = f"{current}\n\n{para}" if current else para
    if current:
        chunks.append(current)
    return [f"[{title}]\n{c}" for c in chunks]


def main() -> None:
    client = OpenAI()

    records = []
    for path in sorted(DATA_DIR.glob("*.md")):
        for i, chunk in enumerate(chunk_markdown(path.read_text())):
            records.append((path.name, i, chunk))

    print(f"Embedding {len(records)} chunks with {EMBED_MODEL} ...")
    resp = client.embeddings.create(model=EMBED_MODEL, input=[r[2] for r in records])
    embeddings = [d.embedding for d in resp.data]

    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        conn.execute(SCHEMA)
        register_vector(conn)
        # Full refresh keeps re-runs idempotent for this small corpus.
        conn.execute("TRUNCATE chunks")
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO chunks (source, chunk_idx, content, embedding) VALUES (%s, %s, %s, %s)",
                [(src, idx, text, emb) for (src, idx, text), emb in zip(records, embeddings)],
            )
        count = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
    print(f"Stored {count} chunks in Postgres.")


if __name__ == "__main__":
    main()
