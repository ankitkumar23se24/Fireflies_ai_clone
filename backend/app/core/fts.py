"""SQLite FTS5 index for transcript text (external-content table kept in sync by triggers)."""
from sqlalchemy import text
from sqlalchemy.engine import Connection

FTS_STATEMENTS = [
    """CREATE VIRTUAL TABLE IF NOT EXISTS transcript_fts USING fts5(
        text, content='transcript_segments', content_rowid='id', tokenize='porter unicode61')""",
    """CREATE TRIGGER IF NOT EXISTS transcript_fts_ai AFTER INSERT ON transcript_segments BEGIN
        INSERT INTO transcript_fts(rowid, text) VALUES (new.id, new.text); END""",
    """CREATE TRIGGER IF NOT EXISTS transcript_fts_ad AFTER DELETE ON transcript_segments BEGIN
        INSERT INTO transcript_fts(transcript_fts, rowid, text) VALUES ('delete', old.id, old.text); END""",
    """CREATE TRIGGER IF NOT EXISTS transcript_fts_au AFTER UPDATE ON transcript_segments BEGIN
        INSERT INTO transcript_fts(transcript_fts, rowid, text) VALUES ('delete', old.id, old.text);
        INSERT INTO transcript_fts(rowid, text) VALUES (new.id, new.text); END""",
]


def create_fts(conn: Connection) -> None:
    for stmt in FTS_STATEMENTS:
        conn.execute(text(stmt))


def drop_fts(conn: Connection) -> None:
    for t in ("transcript_fts_ai", "transcript_fts_ad", "transcript_fts_au"):
        conn.execute(text(f"DROP TRIGGER IF EXISTS {t}"))
    conn.execute(text("DROP TABLE IF EXISTS transcript_fts"))


def fts_available(conn: Connection) -> bool:
    row = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='transcript_fts'")
    ).first()
    return row is not None


def build_match_query(q: str) -> str:
    """Turn free text into a safe FTS5 query: quoted prefix tokens, AND-ed."""
    tokens = ["".join(ch for ch in t if ch.isalnum()) for t in q.split()]
    tokens = [t for t in tokens if t]
    return " ".join(f'"{t}"*' for t in tokens)
