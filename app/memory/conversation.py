from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "synora.db"


class ConversationMemory:
    """
    Local SQLite memory system.

    Stores:
    1. Conversation history
    2. Explicit long-term memories
    """

    def __init__(self, db_path: str | Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _initialize_database(self):
        with self._connect() as connection:

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

            connection.commit()

    # ==========================================================
    # CONVERSATION MEMORY
    # ==========================================================

    def add_message(self, role: str, content: str):
        """Store a conversation message."""

        role = str(role).strip().lower()
        content = str(content).strip()

        if not role or not content:
            return

        timestamp = datetime.now().isoformat(timespec="seconds")

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO conversations (role, content, created_at)
                VALUES (?, ?, ?)
                """,
                (role, content, timestamp),
            )

            connection.commit()

    def get_recent_messages(self, limit: int = 10) -> list[dict]:
        """Return recent conversation messages chronologically."""

        limit = max(1, min(int(limit), 100))

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content, created_at
                FROM conversations
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        rows.reverse()

        return [
            {
                "role": role,
                "content": content,
                "created_at": created_at,
            }
            for role, content, created_at in rows
        ]

    def clear_conversations(self):
        """Delete conversation history without deleting long-term memories."""

        with self._connect() as connection:
            connection.execute("DELETE FROM conversations")
            connection.commit()

    def count_conversations(self) -> int:
        """Return the number of stored conversation messages."""

        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM conversations"
            ).fetchone()

        return int(row[0])

    # ==========================================================
    # LONG-TERM MEMORY
    # ==========================================================

    def add_memory(self, memory: str) -> bool:
        """
        Store an explicit long-term memory.

        Returns:
            True  -> memory was added
            False -> memory already existed or was empty
        """

        memory = str(memory).strip()

        if not memory:
            return False

        timestamp = datetime.now().isoformat(timespec="seconds")

        with self._connect() as connection:
            try:
                connection.execute(
                    """
                    INSERT INTO memories (memory, created_at, updated_at)
                    VALUES (?, ?, ?)
                    """,
                    (memory, timestamp, timestamp),
                )

                connection.commit()
                return True

            except sqlite3.IntegrityError:
                return False

    def get_memories(self, limit: int = 50) -> list[dict]:
        """Return stored long-term memories."""

        limit = max(1, min(int(limit), 200))

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, memory, created_at, updated_at
                FROM memories
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "id": row[0],
                "memory": row[1],
                "created_at": row[2],
                "updated_at": row[3],
            }
            for row in rows
        ]

    def delete_memory(self, memory_id: int) -> bool:
        """Delete a long-term memory by ID."""

        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM memories WHERE id = ?",
                (memory_id,),
            )

            connection.commit()

        return cursor.rowcount > 0

    def clear_memories(self):
        """Delete all long-term memories."""

        with self._connect() as connection:
            connection.execute("DELETE FROM memories")
            connection.commit()

    def count_memories(self) -> int:
        """Return the number of stored long-term memories."""

        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM memories"
            ).fetchone()

        return int(row[0])


# ==============================================================
# UI / APPLICATION COMPATIBILITY HELPERS
# ==============================================================

def build_memory_context(limit: int = 10) -> str:
    """
    Build a compact text representation of recent conversation
    history for Synora's LLM context.

    This is intentionally a module-level helper so other parts
    of Synora can import it directly.
    """

    memory = ConversationMemory()

    messages = memory.get_recent_messages(limit=limit)

    if not messages:
        return ""

    lines = []

    for message in messages:
        role = str(message.get("role", "")).strip()
        content = str(message.get("content", "")).strip()

        if not role or not content:
            continue

        lines.append(f"{role}: {content}")

    return "\n".join(lines)


# ==============================================================
# DIRECT TEST
# ==============================================================

if __name__ == "__main__":

    memory = ConversationMemory()

    print("\nSynora Memory Test")
    print("=" * 50)

    # Test conversation memory.
    memory.add_message("user", "Hello Synora.")
    memory.add_message(
        "assistant",
        "Hello! How can I help you?"
    )

    print("\nRecent conversation:")

    for message in memory.get_recent_messages():
        print(
            f"{message['role']}: "
            f"{message['content']}"
        )

    # Test long-term memory.
    test_memory = (
        "User's favourite programming language is Python."
    )

    added = memory.add_memory(test_memory)

    print("\nLong-term memory:")
    print(f"Added: {added}")

    for item in memory.get_memories():
        print(
            f"[{item['id']}] "
            f"{item['memory']}"
        )

    print("\nStatistics:")
    print(
        f"Conversation messages: "
        f"{memory.count_conversations()}"
    )
    print(
        f"Long-term memories: "
        f"{memory.count_memories()}"
    )

    print(
        f"\nDatabase: "
        f"{memory.db_path}"
    )

    print("\nMemory context:")
    print(build_memory_context())