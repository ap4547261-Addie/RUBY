from memory.short_term import ShortTermMemory
from memory.memory_consolidation import MemoryConsolidation
from ruby_core.development import Development
from emotion.emotion_engine import EmotionEngine
from emotion.emotion_expression import EmotionExpression
from identity.identity_development import IdentityDevelopment
from social.social_learning import SocialLearning
from reflection.reflection_engine import ReflectionEngine
from motivation.motivation_engine import MotivationEngine
from cognition.cognition_engine import CognitionEngine
from learning.learning_engine import LearningEngine
from personality.personality_development import PersonalityDevelopment

# V1.5 — optional
try:
    from evolution.development_engine import DevelopmentEngine
    EVOLUTION_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Evolution layer not available: {e}")
    EVOLUTION_AVAILABLE = False
    DevelopmentEngine = None

# V1.6 — optional
try:
    from integrations.integration_engine import IntegrationEngine
    INTEGRATIONS_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Integrations layer not available: {e}")
    INTEGRATIONS_AVAILABLE = False
    IntegrationEngine = None


class ResponseEngine:
    def __init__(self, brain, user_name="not_set", platform="private"):
        self.brain = brain
        self.user_name = user_name
        self.platform = platform
        self.short_term = ShortTermMemory(max_messages=10)
        self.memory = MemoryConsolidation(user_name=user_name)
        self.dev = Development(user_name=user_name)
        self.emotion = EmotionEngine(user_name=user_name)
        self.emotion_expr = EmotionExpression()
        self.identity = IdentityDevelopment(user_name=user_name)
        self.social = SocialLearning(subject=user_name)
        self.reflection = ReflectionEngine(user_name=user_name)
        self.motivation = MotivationEngine(user_name=user_name, platform=platform)
        self.cognition = CognitionEngine(user_name=user_name)
        self.learning = LearningEngine(user_name=user_name)
        self.personality = PersonalityDevelopment(user_name=user_name)

        # V1.5
        if EVOLUTION_AVAILABLE:
            try:
                self.evolution = DevelopmentEngine(user_name=user_name)
            except Exception as e:
                print(f"⚠️ Evolution init failed: {e}")
                self.evolution = None
        else:
            self.evolution = None

        # V1.6
        if INTEGRATIONS_AVAILABLE:
            try:
                self.integrations = IntegrationEngine(user_name=user_name)
            except Exception as e:
                print(f"⚠️ Integrations init failed: {e}")
                self.integrations = None
        else:
            self.integrations = None

    def respond(self, user_message: str, ruby_prompt: str) -> str:
        # V1.3 — evaluate last prediction
        try:
            self.learning.pre_turn(user_message)
        except Exception as e:
            print(f"⚠️ learning.pre_turn failed: {e}")

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

        try:
            personality_line = self.personality.describe()
            context = f"{context}\n\n{personality_line}"
        except Exception as e:
            print(f"⚠️ personality.describe failed: {e}")

        if self.evolution:
            try:
                values_line = self.evolution.describe()
                if values_line:
                    context = f"{context}\n\n{values_line}"
            except Exception as e:
                print(f"⚠️ evolution.describe failed: {e}")

        # V1.6 — semantic memory from Pinecone
        if self.integrations:
            try:
                semantic_line = self.integrations.build_context(user_message)
                if semantic_line:
                    context = f"{context}\n\n{semantic_line}"
            except Exception as e:
                print(f"⚠️ integrations.build_context failed: {e}")

        try:
            learning_line = self.learning.describe()
            if learning_line:
                context = f"{context}\n\nWhat you've learned from experience: {learning_line}"
        except Exception as e:
            print(f"⚠️ learning.describe failed: {e}")

        # V1.2 — cognition
        trace = None
        try:
            rel = self.memory.relationship.get_state()
            inner = self.dev.state.get()
            trace = self.cognition.process(
                user_message,
                context={
                    "trust": rel["trust"],
                    "attachment": rel["attachment"],
                    "warmth": inner["warmth"],
                    "irritation": inner["irritation"],
                },
            )
            cognition_line = self.cognition.describe(trace)
            context = f"{context}\n\nYour thinking:\n{cognition_line}"
        except Exception as e:
            print(f"⚠️ cognition.process failed: {e}")

        # Format prompt
        try:
            base_prompt = ruby_prompt.format(user_name=self.user_name)
        except Exception:
            base_prompt = ruby_prompt

        description = base_prompt
        if context:
            description = f"{base_prompt}\n\n{context}"

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

        # 12. V1.4
        try:
            rel = self.memory.relationship.get_state()
            emo = self.emotion.get_all()
            inner = self.dev.state.get()
            self.personality.process(
                internal_state=inner,
                emotions=emo,
                relationship=rel,
                learning=None,
            )
        except Exception as e:
            print(f"⚠️ personality.process failed: {e}")

        # 13. V1.5
        if self.evolution:
            try:
                rel = self.memory.relationship.get_state()
                emo = self.emotion.get_all()
                inner = self.dev.state.get()
                self.evolution.process(
                    internal_state=inner,
                    emotions=emo,
                    relationship=rel,
                    learning=None,
                )
            except Exception as e:
                print(f"⚠️ evolution.process failed: {e}")

        # 14. V1.6 — store in Pinecone
        if self.integrations:
            try:
                self.integrations.process(user_message, reply)
            except Exception as e:
                print(f"⚠️ integrations.process failed: {e}")

        # 15. V1.3 — learning
        try:
            emo = self.emotion.get_all()
            if trace is not None:
                self.learning.post_turn(trace, user_message, reply, emo)
        except Exception as e:
            print(f"⚠️ learning.post_turn failed: {e}")

        return reply

    def clear_short_term(self):
        self.short_term.clear()

    def wipe_all_memory(self):
        self.short_term.clear()
        self.memory.wipe_all()
        for name, obj in [
            ("dev", self.dev),
            ("emotion", self.emotion),
            ("identity", self.identity),
            ("social", self.social),
            ("reflection", self.reflection),
            ("motivation", self.motivation),
            ("cognition", self.cognition),
            ("learning", self.learning),
            ("personality", self.personality),
        ]:
            try:
                obj.wipe()
            except Exception:
                pass
        if self.evolution:
            try:
                self.evolution.wipe()
            except Exception:
                pass
        if self.integrations:
            try:
                self.integrations.wipe()
            except Exception:
                pass
        try:
            from social.interaction_history import InteractionHistory
            InteractionHistory().wipe()
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

    def cognition_trace(self):
        return self.cognition.last_trace()

    def learning_summary(self):
        return self.learning.error_summary()

    def recent_prediction_errors(self, limit=10):
        return self.learning.recent_errors(limit=limit)

    def preference_stats(self):
        return self.learning.preferences()

    def best_behaviors(self, limit=5):
        return self.learning.best_behaviors(limit=limit)

    def worst_behaviors(self, limit=5):
        return self.learning.worst_behaviors(limit=limit)

    def personality_stats(self):
        return self.personality.traits()

    def values_stats(self):
        return self.evolution.get_values() if self.evolution else {}

    def value_history(self, limit=None):
        return self.evolution.get_value_history(limit=limit) if self.evolution else []

    def evolution_personality(self):
        return self.evolution.get_personality() if self.evolution else {}

    def evolution_preferences(self):
        return self.evolution.get_preferences() if self.evolution else []

    # V1.6
    def integration_stats(self):
        return self.integrations.stats() if self.integrations else {}
