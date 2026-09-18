import os
import shutil
from datetime import datetime


class CloudSync:
    """
    Backs up Ruby's local database (SQLite) to a local folder.
    Cloud upload can be added later.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name

        storage_dir = os.getenv("FLET_APP_STORAGE_DATA", ".")
        self.backup_dir = os.path.join(storage_dir, "backups")
        os.makedirs(self.backup_dir, exist_ok=True)

        self.db_path = os.path.join(storage_dir, "ruby_memory.db")

    def backup_database(self):
        if not os.path.exists(self.db_path):
            print("ℹ️ No database to back up yet.")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = os.path.join(self.backup_dir, f"ruby_memory_{timestamp}.db")

        try:
            shutil.copy(self.db_path, target)
            print(f"💾 DB backed up: {target}")
            return target
        except Exception as e:
            print(f"⚠️ Backup failed: {e}")
            return None

    def list_backups(self):
        if not os.path.exists(self.backup_dir):
            return []
        files = [
            os.path.join(self.backup_dir, f)
            for f in os.listdir(self.backup_dir)
            if f.endswith(".db")
        ]
        files.sort(reverse=True)
        return files

    def restore_latest(self):
        backups = self.list_backups()
        if not backups:
            print("ℹ️ No backups found.")
            return False
        latest = backups[0]
        try:
            shutil.copy(latest, self.db_path)
            print(f"♻️ Restored from: {latest}")
            return True
        except Exception as e:
            print(f"⚠️ Restore failed: {e}")
            return False

    def stats(self):
        return {
            "backup_count": len(self.list_backups()),
            "backup_dir": self.backup_dir,
        }

    def wipe(self):
        try:
            for f in self.list_backups():
                os.remove(f)
            print("🗑️ All backups cleared.")
        except Exception as e:
            print(f"⚠️ Backup wipe failed: {e}")
