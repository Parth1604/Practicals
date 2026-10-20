"""Interactive CLI: ask questions about Nimbus Coffee Co."""
from rag import answer


def main() -> None:
    print("Nimbus Coffee RAG — ask a question (type 'exit' to quit)")
    while True:
        try:
            q = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            continue
        if q.lower() in {"exit", "quit"}:
            break
        result = answer(q)
        print(f"\nbot> {result.answer}")
        sources = ", ".join(sorted({c.source for c in result.contexts}))
        print(f"     sources: {sources}")


if __name__ == "__main__":
    main()
