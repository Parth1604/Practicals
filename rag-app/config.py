import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://rag:rag@localhost:5432/ragdb")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
EVAL_MODEL = os.getenv("EVAL_MODEL", "gpt-4o-mini")
TOP_K = int(os.getenv("TOP_K", "4"))
