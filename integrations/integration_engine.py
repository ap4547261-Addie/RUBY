from integrations.pinecone_memory import PineconeMemory
from integrations.cloud_sync import CloudSync


class IntegrationEngine:
    """
    Coordinates external integrations: Pinecone + cloud backups.
    Both are optional. If unavailable, Ruby works with SQLite only.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self.pinecone = PineconeMemory(user_name=user_name)
        self.cloud = CloudSync(user_name=user_name)

    def process(self, user_message, ruby_reply):
        if self.pinecone.is_enabled():
            self.pinecone.store(user_message, ruby_reply)

    def build_context(self, user_message):
        return self.pinecone.build_context(user_message, limit=3)

    def backup(self):
        return self.cloud.backup_database()

    def describe(self):
        if not self.pinecone.is_enabled():
            return ""
        stats = self.pinecone.stats()
        if stats.get("status") != "connected":
            return ""
        return f"Semantic memory: {stats.get('total_vectors', 0)} vectors stored."

    def stats(self):
        return {
            "pinecone": self.pinecone.stats(),
            "cloud": self.cloud.stats(),
        }

    def wipe(self):
        self.pinecone.wipe()
        self.cloud.wipe()
