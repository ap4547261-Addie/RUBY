class Priorities:
    """
    Ranks Ruby's drives by raw value.
    No multipliers. No thresholds. No top-N cut.
    Every drive reaches the prompt.
    Platform filters only lust — nothing else.
    """

    def rank(self, drives: dict) -> list:
        if not drives:
            return []
        return sorted(drives.items(), key=lambda x: -x[1])

    def top(self, drives: dict):
        ranked = self.rank(drives)
        if not ranked:
            return (None, 0.0)
        return ranked[0]

    def describe(self, drives: dict, platform: str = "private") -> str:
        """
        Describe ALL drives with a value > 0.
        Only lust is filtered on non-private platforms.
        """
        ranked = self.rank(drives)

        if platform != "private":
            ranked = [(n, v) for n, v in ranked if n != "lust"]

        lines = [f"{name} ({round(w, 1)})" for name, w in ranked if w > 0]

        if not lines:
            return "No active drives."

        # most pressing stays visible for clarity, but every drive is listed
        most = ranked[0] if ranked else (None, 0.0)
        return "Drives: " + ", ".join(lines) + f". Most pressing: {most[0]} ({round(most[1], 1)})."
