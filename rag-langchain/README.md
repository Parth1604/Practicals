# Nimbus Coffee RAG — LangChain + LangGraph version

The same app as [`../rag-app`](../rag-app) (same docs, same Postgres + pgvector, same OpenAI
models, same DeepEval golden set), rebuilt with LangChain components and a LangGraph
state machine.

## The graph

```
START → retrieve → grade_documents ─┬─(some docs relevant)──────────► generate → END
            ▲                       ├─(none relevant, rewrites left)─► rewrite_query ─┐
            └───────────────────────┼─────────────────────────────────────────────────┘
                                    └─(none relevant, out of rewrites)► fallback → END
```

| Node | What it does |
|---|---|
| `retrieve` | `PGVector` retriever, top-4 by cosine similarity |
| `grade_documents` | `gpt-4o-mini` with structured output (`Grade.relevant: bool`) grades each chunk in parallel; irrelevant chunks are dropped |
| `rewrite_query` | Rewrites the question into a better search query (at most `MAX_REWRITES`, default 1) |
| `generate` | Answers only from the graded chunks |
| `fallback` | Returns "I don't know based on the Nimbus documents." without calling the LLM |

## What changed vs. `rag-app`

| | `rag-app` (plain Python) | `rag-langchain` |
|---|---|---|
| Chunking | Paragraph packing, 500 chars → 16 chunks | `MarkdownHeaderTextSplitter` + `RecursiveCharacterTextSplitter` (500/50) → 27 chunks, one per section |
| Vector store | Own `chunks` table + HNSW index | `langchain_postgres.PGVector` (tables `langchain_pg_collection` / `langchain_pg_embedding`, collection `nimbus_docs`) |
| Pipeline | `retrieve()` → `answer()` | LangGraph `StateGraph` with grading, query rewrite loop, and fallback |
| Off-topic questions | LLM is told to say "I don't know" | Grader filters everything out → `fallback` node, no generation call |

## Run it

Uses the same database as `rag-app`. Both apps can share it, since they use different tables.

```bash
cd rag-app && docker compose up -d && cd ..     # Postgres + pgvector
cd rag-langchain
cp .env.example .env                            # add OPENAI_API_KEY
pip install -r requirements.txt

python ingest.py                                # 27 chunks → collection 'nimbus_docs'
python chat.py                                  # shows sources and any rewritten query
deepeval test run eval/test_rag.py              # same 10 golden questions + 4 metrics
```

## Things to try

- **Comparison questions** ("What's the cheapest bag of beans?") currently get "I don't know":
  each coffee is its own chunk and only one lands in the top 4. Try `TOP_K=8`, or merge
  sections back together in `ingest.py`, then re-run the eval.
- Set `MAX_REWRITES=0` to disable the rewrite loop and compare latency and cost.
- If DeepEval reports `Timed out` or `LengthFinishReasonError` on Faithfulness, the judge LLM
  failed to produce output, not your app. Re-run that test
  (`deepeval test run eval/test_rag.py -k "<words>"`) or raise
  `DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE`.
