from datetime import datetime
from emotion.emotion_state import EmotionState
from emotion.emotion_appraisal import EmotionAppraisal


class EmotionEngine:
    """
    Coordinates emotion state + appraisal + decay.
    Called on every message.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self.state = EmotionState(user_name=user_name)
        self.appraisal = EmotionAppraisal()
        self._last_tick = None

    def _tick_time_decay(self):
        """Apply time-based decay since last message."""
        conn = self.state.get_all()
        if not conn:
            return
        # pull last_updated from db (cheap)
        from memory import database
        db = database.get_connection()
        c = db.cursor()
        c.execute("SELECT last_updated FROM emotions WHERE user_name = ?",
                  (self.user_name,))
        row = c.fetchone()
        db.close()
        if not row or not row[0]:
            return
        try:
            last = datetime.fromisoformat(row[0])
            hours = (datetime.now() - last).total_seconds() / 3600
            if hours > 0.1:
                self.state.decay(hours)
        except Exception:
            pass

    def process(self, user_message, context):
        """
        Called after every user message.
        context = {trust, attachment, warmth, irritation, message_count}
        """
        # 1. apply time decay first
        self._tick_time_decay()

        # 2. appraise the new message
        deltas = self.appraisal.appraise(user_message, context)

        # 3. apply
        self.state.add_many(deltas)

        return deltas

    def get_all(self):
        return self.state.get_all()

    def dominant(self):
        return self.state.dominant()

    def wipe(self):
        self.state.wipe()
