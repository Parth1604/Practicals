"""Load the Markdown docs, split them, embed with OpenAI, and store them in pgvector via LangChain."""
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from config import DATA_DIR
from store import get_vector_store

header_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#", "title"), ("##", "section")], strip_headers=False
)
size_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)


def load_chunks() -> list[Document]:
    chunks = []
    for path in sorted(DATA_DIR.glob("*.md")):
        sections = header_splitter.split_text(path.read_text())
        for doc in size_splitter.split_documents(sections):
            doc.metadata["source"] = path.name
            # Prefix the title so every chunk stays meaningful on its own.
            title = doc.metadata.get("title", "")
            if title and not doc.page_content.startswith("# "):
                doc.page_content = f"[{title}]\n{doc.page_content}"
            chunks.append(doc)
    return chunks


def main() -> None:
    chunks = load_chunks()
    print(f"Embedding {len(chunks)} chunks ...")
    # Recreating the collection keeps re-runs idempotent for this small corpus.
    store = get_vector_store(pre_delete_collection=True)
    store.add_documents(chunks)
    print(f"Stored {len(chunks)} chunks in Postgres (collection '{store.collection_name}').")


if __name__ == "__main__":
    main()
