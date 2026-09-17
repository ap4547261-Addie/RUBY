from memory.short_term import ShortTermMemory
from memory.memory_consolidation import MemoryConsolidation
from ruby_core.development import Development
from emotion.emotion_engine import EmotionEngine
from emotion.emotion_expression import EmotionExpression
from identity.identity_development import IdentityDevelopment
from social.social_learning import SocialLearning
from reflection.reflection_engine import ReflectionEngine
from motivation.motivation_engine import MotivationEngine


class ResponseEngine:
    def __init__(self, brain, user_name="not_set", platform="private"):
        self.brain = brain
        self.user_name = user_name
        self.platform = platform
        self.short_term = ShortTermMemory(max_messages=10)
        self.memory = MemoryConsolidation(user_name=user_name)
        self.dev = Development(user_name=user_name)                    # V0.5
        self.emotion = EmotionEngine(user_name=user_name)              # V0.6
        self.emotion_expr = EmotionExpression()                        # V0.6
        self.identity = IdentityDevelopment(user_name=user_name)       # V0.7
        self.social = SocialLearning(subject=user_name)                # V0.8
        self.reflection = ReflectionEngine(user_name=user_name)        # V0.9
        self.motivation = MotivationEngine(user_name=user_name, platform=platform)  # V1.0

    def respond(self, user_message: str, ruby_prompt: str) -> str:
        # 1. Build context
        context = self.memory.build_context(user_message)

        try:
            inner_line = self.dev.describe()
            context = f"{context}\n\nYour body and mood: {inner_line}"
        except Exception as e:
            print(f"⚠️ dev.describe failed: {e}")

        try:
            emotions = self.emotion.get_all()
            emotion_line = self.emotion_expr.describe(emotions)
            context = f"{context}\n\nYour feelings right now: {emotion_line}"
        except Exception as e:
            print(f"⚠️ emotion.describe failed: {e}")

        try:
            identity_line = self.identity.describe()
            context = f"{context}\n\n{identity_line}"
        except Exception as e:
            print(f"⚠️ identity.describe failed: {e}")

        try:
            social_line = self.social.describe()
            context = f"{context}\n\nWho he is to you:\n{social_line}"
        except Exception as e:
            print(f"⚠️ social.describe failed: {e}")

        try:
            drive_line = self.motivation.describe()
            context = f"{context}\n\nWhat you need right now: {drive_line}"
        except Exception as e:
            print(f"⚠️ motivation.describe failed: {e}")

        description = ruby_prompt
        if context:
            description = f"{ruby_prompt}\n\n{context}"

        # 2. Short-term
        self.short_term.add("user", user_message)

        # 3. Generate
        reply = self.brain.generate(
            description=description,
            history=self.short_term.get_messages(),
            user_name=self.user_name,
        )

        # 4. Store reply
        self.short_term.add("assistant", reply)

        # 5. Long-term memory
        self.memory.process(user_message, reply)

        # 6. V0.5
        try:
            self.dev.tick()
            rel = self.memory.relationship.get_state()
            self.dev.on_message(
                user_message, reply,
                trust=rel["trust"],
                attachment=rel["attachment"],
            )
        except Exception as e:
            print(f"⚠️ dev.on_message failed: {e}")

        # 7. V0.6
        try:
            rel = self.memory.relationship.get_state()
            inner = self.dev.state.get()
            self.emotion.process(
                user_message,
                context={
                    "trust": rel["trust"],
                    "attachment": rel["attachment"],
                    "warmth": inner["warmth"],
                    "irritation": inner["irritation"],
                    "message_count": rel["message_count"],
                },
            )
        except Exception as e:
            print(f"⚠️ emotion.process failed: {e}")

        # 8. V0.7
        try:
            rel = self.memory.relationship.get_state()
            emo = self.emotion.get_all()
            inner = self.dev.state.get()
            self.identity.process(
                user_message, reply,
                context={
                    "trust": rel["trust"],
                    "attachment": rel["attachment"],
                    "emotions": emo,
                    "irritation": inner["irritation"],
                    "warmth": inner["warmth"],
                },
            )
        except Exception as e:
            print(f"⚠️ identity.process failed: {e}")

        # 9. V0.8
        try:
            rel = self.memory.relationship.get_state()
            emo = self.emotion.get_all()
            inner = self.dev.state.get()
            self.social.process(
                user_message, reply,
                context={
                    "trust": rel["trust"],
                    "attachment": rel["attachment"],
                    "emotions": emo,
                    "internal_state": inner,
                },
            )
        except Exception as e:
            print(f"⚠️ social.process failed: {e}")

        # 10. V0.9
        try:
            rel = self.memory.relationship.get_state()
            emo = self.emotion.get_all()
            inner = self.dev.state.get()
            beliefs = self.identity.beliefs()
            self.reflection.process(
                internal_state=inner,
                emotions=emo,
                beliefs=beliefs,
                message_count=rel["message_count"],
            )
        except Exception as e:
            print(f"⚠️ reflection.process failed: {e}")

        # 11. V1.0
        try:
            rel = self.memory.relationship.get_state()
            emo = self.emotion.get_all()
            inner = self.dev.state.get()
            self.motivation.process(
                user_message,
                context={
                    "trust": rel["trust"],
                    "attachment": rel["attachment"],
                    "emotions": emo,
                    "internal_state": inner,
                },
            )
        except Exception as e:
            print(f"⚠️ motivation.process failed: {e}")

        return reply

    # ----------------------------------------
    # Utilities
    # ----------------------------------------
    def clear_short_term(self):
        self.short_term.clear()

    def wipe_all_memory(self):
        self.short_term.clear()
        self.memory.wipe_all()
        try:
            self.dev.wipe()
        except Exception:
            pass
        try:
            self.emotion.wipe()
        except Exception:
            pass
        try:
            self.identity.wipe()
        except Exception:
            pass
        try:
            self.social.wipe()
        except Exception:
            pass
        try:
            from social.interaction_history import InteractionHistory
            InteractionHistory().wipe()
        except Exception:
            pass
        try:
            self.reflection.wipe()
        except Exception:
            pass
        try:
            self.motivation.wipe()
        except Exception:
            pass

    def memory_stats(self):
        return self.memory.stats()

    def emotion_stats(self):
        return self.emotion.get_all()

    def internal_state_stats(self):
        return self.dev.state.get()

    def identity_stats(self):
        return self.identity.beliefs()

    def identity_history(self):
        return self.identity.history_recent(limit=40)

    def social_stats(self):
        return self.social.model.get()

    def reflection_stats(self):
        return self.reflection.counts()

    def reflections_recent(self, limit=None):
        return self.reflection.recent_reflections(limit=limit)

    def experience_reviews_recent(self, limit=None):
        return self.reflection.recent_experience_reviews(limit=limit)

    def long_term_reflections_recent(self, limit=None):
        return self.reflection.recent_long_term(limit=limit)

    def drives_stats(self):
        return self.motivation.get_all()
