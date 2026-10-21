from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from config import COLLECTION, DATABASE_URL, EMBED_MODEL


def get_vector_store(pre_delete_collection: bool = False) -> PGVector:
    return PGVector(
        # Chunks are tiny, so skip the tiktoken length check (it downloads an encoding file).
        embeddings=OpenAIEmbeddings(model=EMBED_MODEL, check_embedding_ctx_length=False),
        collection_name=COLLECTION,
        connection=DATABASE_URL,
        use_jsonb=True,
        pre_delete_collection=pre_delete_collection,
    )
