# Nimbus Coffee RAG (pgvector + OpenAI + DeepEval)

A very small Retrieval-Augmented Generation app over a fictional company's docs
(`data/*.md` — "Nimbus Coffee Co."). The company is made up, so the LLM can only
answer correctly by retrieving from the database.

```
data/*.md ─► chunk (~500 chars) ─► OpenAI text-embedding-3-small (1536-d)
                                          │
                                          ▼
                     PostgreSQL + pgvector (chunks table, HNSW cosine index)
                                          │
question ─► embed ─► top-4 by cosine ─────┘─► gpt-4o-mini (answer only from context)
```

| File | Purpose |
|---|---|
| `docker-compose.yml`, `db/init.sql` | Postgres 16 + pgvector, schema, HNSW index |
| `ingest.py` | Chunk → embed → store (full refresh, safe to re-run) |
| `rag.py` | `retrieve()` and `answer()` |
| `chat.py` | Interactive CLI |
| `eval/golden.json`, `eval/test_rag.py` | DeepEval tests |

## Run it

```bash
cd rag-app
cp .env.example .env            # put your OPENAI_API_KEY in .env
docker compose up -d            # Postgres + pgvector on localhost:5432
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python ingest.py                # embeds 16 chunks and stores them
python chat.py                  # ask questions
```

Example questions: *How much is a 16 oz latte?* · *Is shipping free?* ·
*What's the V60 recipe?* · *Who is the CEO?* · *Do you sell tea?* (should say "I don't know").

## Evaluate with DeepEval

```bash
deepeval test run eval/test_rag.py
```

Each of the 10 golden questions is run through the pipeline and scored by an LLM judge
(`EVAL_MODEL`, default `gpt-4o-mini`) on:

| Metric | Measures | Part tested |
|---|---|---|
| Answer Relevancy | Does the answer address the question? | Generation |
| Faithfulness | Is every claim supported by the retrieved chunks? (hallucination check) | Generation |
| Contextual Precision | Are the relevant chunks ranked above irrelevant ones? | Retrieval |
| Contextual Recall | Do the retrieved chunks contain everything in the expected answer? | Retrieval |

A test passes when all four scores are ≥ 0.7. Things to try: change `TOP_K`,
`MAX_CHARS` in `ingest.py`, or the system prompt, then re-run the eval and compare.

## Inspect the vectors

```bash
docker exec -it rag-postgres psql -U rag -d ragdb \
  -c "SELECT source, chunk_idx, left(content, 60), vector_dims(embedding) FROM chunks;"
```
