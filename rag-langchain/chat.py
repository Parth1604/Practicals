"""Interactive CLI for the LangGraph RAG pipeline."""
from graph import ask


def main() -> None:
    print("Nimbus Coffee RAG (LangChain + LangGraph) — ask a question (type 'exit' to quit)")
    while True:
        try:
            q = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            continue
        if q.lower() in {"exit", "quit"}:
            break
        result = ask(q)
        print(f"\nbot> {result['answer']}")
        if result["query"] != q:
            print(f"     rewritten query: {result['query']}")
        sources = ", ".join(sorted({d.metadata['source'] for d in result["documents"]})) or "none relevant"
        print(f"     sources: {sources}")


if __name__ == "__main__":
    main()
