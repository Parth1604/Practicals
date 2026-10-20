CREATE EXTENSION IF NOT EXISTS vector;

-- text-embedding-3-small produces 1536-dimensional vectors
CREATE TABLE IF NOT EXISTS chunks (
    id        BIGSERIAL PRIMARY KEY,
    source    TEXT NOT NULL,
    chunk_idx INT  NOT NULL,
    content   TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    UNIQUE (source, chunk_idx)
);

CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw
    ON chunks USING hnsw (embedding vector_cosine_ops);
