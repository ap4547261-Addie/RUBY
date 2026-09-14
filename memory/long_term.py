from datetime import datetime
from memory import database


class LongTermMemory:
    """Handles persistent memory via SQLite."""

    def __init__(self):
        database.init_db()

    # -------------------------
    # Save
    # -------------------------
    def remember(self, user_message: str, ruby_reply: str,
                 category: str = "conversation", importance: int = 3):
        timestamp = datetime.now().isoformat(timespec="seconds")
        database.insert_memory(
            user_message=user_message,
            ruby_reply=ruby_reply,
            timestamp=timestamp,
            category=category,
            importance=importance,
        )

    # -------------------------
    # Retrieve
    # -------------------------
    def get_relevant_context(self, user_message: str, limit: int = 3) -> str:
        """
        Returns a short text block of relevant past memories,
        ready to be injected into the prompt.
        """
        # 1. Try keyword search on meaningful words
        keywords = [w for w in user_message.lower().split() if len(w) >= 4]
        found = []

        for kw in keywords[:2]:  # only check top 2 keywords
            results = database.search_by_keyword(kw, limit=limit)
            for row in results:
                if row not in found:
                    found.append(row)

        # 2. If nothing found, use the most recent memories
        if not found:
            found = database.get_recent(limit=limit)

        if not found:
            return ""

        # 3. Format as a compact context block
        lines = ["[Things you remember from past conversations:]"]
        for user_msg, ruby_reply, ts in found:
            lines.append(f"- Addie said: {user_msg}")
            lines.append(f"  You replied: {ruby_reply}")

        return "\n".join(lines)

    # -------------------------
    # Utilities
    # -------------------------
    def count(self) -> int:
        return database.count_memories()

    def wipe(self):
        database.clear_all()
