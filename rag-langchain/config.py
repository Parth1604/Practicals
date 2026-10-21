import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent
# Same documents and golden set as ../rag-app, so the two implementations are directly comparable.
DATA_DIR = ROOT.parent / "rag-app" / "data"
GOLDEN_PATH = ROOT.parent / "rag-app" / "eval" / "golden.json"

# langchain-postgres connects through SQLAlchemy, hence the +psycopg driver suffix.
DATABASE_URL = os.getenv("LC_DATABASE_URL", "postgresql+psycopg://rag:rag@localhost:5432/ragdb")
COLLECTION = os.getenv("COLLECTION", "nimbus_docs")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
EVAL_MODEL = os.getenv("EVAL_MODEL", "gpt-4o-mini")
TOP_K = int(os.getenv("TOP_K", "4"))
MAX_REWRITES = int(os.getenv("MAX_REWRITES", "1"))
