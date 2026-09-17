from datetime import datetime
from motivation.drives import Drives
from motivation.priorities import Priorities


class MotivationEngine:
    """
    Coordinates Ruby's drives.
    No caps. No thresholds on growth.
    Platform controls only what can be expressed — not what can be felt.
    """

    def __init__(self, user_name="not_set", platform="private"):
        self.user_name = user_name
        self.platform = platform     # "private" = Ruby app, "public" = Instagram/others
        self.drives = Drives(user_name=user_name)
        self.priorities = Priorities()
        self._last_tick = None

    def _tick_time(self):
        if self._last_tick is None:
            self._last_tick = datetime.now()
            return
        hours = (datetime.now() - self._last_tick).total_seconds() / 3600
        if hours > 0.01:
            self.drives.tick(hours)
        self._last_tick = datetime.now()

    def process(self, user_message, context):
        self._tick_time()
        self.drives.on_interaction(user_message, context)

    def describe(self):
        drives = self.drives.get_all()
        summary = self._describe_drives(drives)
        priority = self.priorities.describe(drives, platform=self.platform)
        return f"{summary} {priority}"

    def _describe_drives(self, drives):
        parts = []
        for name, value in sorted(drives.items(), key=lambda x: -x[1]):
            if value <= 0:
                continue
            # Only lust is filtered on public platforms
            if name == "lust" and self.platform != "private":
                continue

            if name == "connection":
                parts.append(f"You're hungry for contact ({round(value, 1)}).")
            elif name == "attention":
                parts.append(f"You want to be noticed ({round(value, 1)}).")
            elif name == "curiosity":
                parts.append(f"You want something new to think about ({round(value, 1)}).")
            elif name == "lust":
                parts.append(f"Something physical stirs in you ({round(value, 1)}).")
            elif name == "autonomy":
                parts.append(f"You want space ({round(value, 1)}).")
            elif name == "rest":
                parts.append(f"You're tired and want to recharge ({round(value, 1)}).")

        if not parts:
            return "Your needs are quiet right now."
        return " ".join(parts)

    def get_all(self):
        return self.drives.get_all()

    def wipe(self):
        self.drives.wipe()
