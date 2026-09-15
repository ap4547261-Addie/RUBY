from datetime import datetime
from memory import database


class LongTermMemory:
    """Persistent memory via SQLite."""

    def __init__(self):
        database.init_db()

    def remember(self, user_message, ruby_reply,
                 category="conversation", importance=3):
        timestamp = datetime.now().isoformat(timespec="seconds")
        database.insert_memory(
            user_message=user_message,
            ruby_reply=ruby_reply,
            timestamp=timestamp,
            category=category,
            importance=importance,
        )

    def get_relevant_context(self, user_message, limit=3) -> str:
        """Return a short text block of relevant past memories."""
        keywords = [w for w in user_message.lower().split() if len(w) >= 4]
        found = []

        for kw in keywords[:2]:
            results = database.search_by_keyword(kw, limit=limit)
            for row in results:
                if row not in found:
                    found.append(row)

        # If nothing relevant found, don't inject random old chats
        if not found:
            return ""

        lines = []
        for user_msg, ruby_reply, ts in found:
            lines.append(f"- they said: {user_msg}")
            lines.append(f"  you replied: {ruby_reply}")

        return "\n".join(lines)

    def count(self) -> int:
        return database.count_memories()

    def wipe(self):
        database.clear_all()
