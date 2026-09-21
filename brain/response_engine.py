# brain/response_engine.py — Ruby V1.9 (MemoryRouter + StoryCache + Goals)

from memory.short_term import ShortTermMemory
from memory.memory_consolidation import MemoryConsolidation
from memory.childhood_memory import ChildhoodMemory
from ruby_core.development import Development
from emotion.emotion_engine import EmotionEngine
from emotion.emotion_expression import EmotionExpression
from identity.identity_development import IdentityDevelopment
from social.social_learning import SocialLearning
from reflection.reflection_engine import ReflectionEngine
from motivation.motivation_engine import MotivationEngine
from cognition.cognition_engine import CognitionEngine
from cognition.curiosity import Curiosity
from learning.learning_engine import LearningEngine
from personality.personality_development import PersonalityDevelopment

# V1.9 — routing + story cache
try:
    from brain.memory_router import get_memory_router
    ROUTER_AVAILABLE = True
except Exception as e:
    print(f"⚠️ MemoryRouter not available: {e}")
    ROUTER_AVAILABLE = False
    get_memory_router = None

try:
    from brain.story_cache import get_story_cache
    STORY_CACHE_AVAILABLE = True
except Exception as e:
    print(f"⚠️ StoryCache not available: {e}")
    STORY_CACHE_AVAILABLE = False
    get_story_cache = None

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

# V1.7 — optional
try:
    from web import Browser, WebLearning, KnowledgeIngestion
    WEB_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Web module not available: {e}")
    WEB_AVAILABLE = False
    Browser = None
    WebLearning = None
    KnowledgeIngestion = None


class ResponseEngine:
    def __init__(self, brain, user_name="not_set", platform="private"):
        self.brain = brain
        self.user_name = user_name
        self.platform = platform
        self.short_term = ShortTermMemory(max_messages=10)
        self.memory = MemoryConsolidation(user_name=user_name)
        self.childhood = ChildhoodMemory(user_name=user_name)
        self.dev = Development(user_name=user_name)
        self.emotion = EmotionEngine(user_name=user_name)
        self.emotion_expr = EmotionExpression()
        self.identity = IdentityDevelopment(user_name=user_name)
        self.social = SocialLearning(subject=user_name)
        self.reflection = ReflectionEngine(user_name=user_name)
        self.motivation = MotivationEngine(user_name=user_name, platform=platform)
        self.cognition = CognitionEngine(user_name=user_name)
        self.curiosity = Curiosity(user_name=user_name)
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

        # V1.7
        if WEB_AVAILABLE:
            try:
                self.web_learning = WebLearning()
                self.web_knowledge = KnowledgeIngestion()
            except Exception as e:
                print(f"⚠️ Web init failed: {e}")
                self.web_learning = None
                self.web_knowledge = None
        else:
            self.web_learning = None
            self.web_knowledge = None

        # V1.9 — Router + StoryCache
        if ROUTER_AVAILABLE:
            try:
                self.router = get_memory_router(user_name=user_name)
            except Exception as e:
                print(f"⚠️ Router init failed: {e}")
                self.router = None
        else:
            self.router = None

        if STORY_CACHE_AVAILABLE:
            try:
                pinecone_mem = None
                if self.integrations is not None:
                    pinecone_mem = getattr(self.integrations, "pinecone", None)
                self.story_cache = get_story_cache(pinecone_mem, user_name=user_name)
            except Exception as e:
                print(f"⚠️ StoryCache init failed: {e}")
                self.story_cache = None
        else:
            self.story_cache = None

    # ============================================================
    # V1.8 — FAST PATH
    # ============================================================
    def respond_fast(self, user_message: str, ruby_prompt: str) -> str:
        # Handles both prompt formats — with or without {context}
        try:
            description = ruby_prompt.format(user_name=self.user_name, context="")
        except Exception:
            try:
                description = ruby_prompt.format(user_name=self.user_name)
            except Exception:
                description = ruby_prompt

        self.short_term.add("user", user_message)
        try:
            reply = self.brain.generate(
                description=description,
                history=self.short_term.get_messages(),
                user_name=self.user_name,
            )
        except Exception as e:
            print(f"⚠️ respond_fast failed: {e}")
            reply = "[FAST ERROR] " + str(e)
        self.short_term.add("assistant", reply)
        return reply

    # ============================================================
    # FULL PATH (System 2) — router-aware
    # ============================================================
    def respond(self, user_message: str, ruby_prompt: str) -> str:
        try:
            self.learning.pre_turn(user_message)
        except Exception as e:
            print(f"⚠️ learning.pre_turn failed: {e}")

        # --------------------------------------------------------
        # V1.9 — retrieval plan
        # --------------------------------------------------------
        plan = {"read_layers": [], "layers": [], "triggers": []}
        if self.router is not None:
            try:
                plan = self.router.plan(user_message)
                print(f"🧭 plan: layers={plan['layers']} budget={plan['token_budget']}")
            except Exception as e:
                print(f"⚠️ router.plan failed: {e}")

        read_layers = set(plan.get("read_layers", []) or [])

        if not self.router:
            read_layers = {
                "episodic", "childhood", "emotion", "identity",
                "social", "motivation", "personality", "cognition_trace",
                "web", "learning", "relationship",
            }

        # --------------------------------------------------------
        # 1. CONTEXT (reads only)
        # --------------------------------------------------------
        context = ""

        # Episodic / relationship
        if "episodic" in read_layers or "relationship" in read_layers:
            try:
                context = self.memory.build_context(user_message)
            except Exception as e:
                print(f"⚠️ memory.build_context failed: {e}")

        # Childhood — story cache first
        childhood_used = False
        if "childhood" in read_layers:
            cached = None
            if self.story_cache is not None:
                try:
                    cached = self.story_cache.lookup(user_message, layer="childhood")
                except Exception as e:
                    print(f"⚠️ story cache lookup failed: {e}")
                    cached = None

            if cached and cached.get("mode") == "hit":
                self.short_term.add("user", user_message)
                self.short_term.add("assistant", cached["story"])
                return cached["story"]

            if cached and cached.get("mode") == "soft":
                context = f"{context}\n\nPreviously told:\n{cached['story']}"
                childhood_used = True
            else:
                try:
                    childhood_line = self.childhood.build_context(user_message, limit=2)
                    if childhood_line:
                        context = f"{context}\n\n{childhood_line}"
                        childhood_used = True
                except Exception as e:
                    print(f"⚠️ childhood.build_context failed: {e}")

        # Dev / body-mood
        try:
            inner_line = self.dev.describe()
            context = f"{context}\n\nYour body and mood: {inner_line}"
        except Exception as e:
            print(f"⚠️ dev.describe failed: {e}")

        # Emotion
        if "emotion" in read_layers:
            try:
                emotions = self.emotion.get_all()
                emotion_line = self.emotion_expr.describe(emotions)
                context = f"{context}\n\nYour feelings right now: {emotion_line}"
            except Exception as e:
                print(f"⚠️ emotion.describe failed: {e}")

        # Identity
        if "identity" in read_layers:
            try:
                identity_line = self.identity.describe()
                context = f"{context}\n\n{identity_line}"
            except Exception as e:
                print(f"⚠️ identity.describe failed: {e}")

        # Social
        if "social" in read_layers:
            try:
                social_line = self.social.describe()
                context = f"{context}\n\nWho he is to you:\n{social_line}"
            except Exception as e:
                print(f"⚠️ social.describe failed: {e}")

        # Motivation
        if "motivation" in read_layers:
            try:
                drive_line = self.motivation.describe()
                context = f"{context}\n\nWhat you need right now: {drive_line}"
            except Exception as e:
                print(f"⚠️ motivation.describe failed: {e}")

        # Personality
        if "personality" in read_layers:
            try:
                personality_line = self.personality.describe()
                context = f"{context}\n\n{personality_line}"
            except Exception as e:
                print(f"⚠️ personality.describe failed: {e}")

        # V1.9 — her direction of growth (goals)
        if ("motivation" in read_layers or "identity" in read_layers) and getattr(self.dev, "goals", None) is not None:
            try:
                goals_line = self.dev.goals.describe()
                if goals_line:
                    context = f"{context}\n\n{goals_line}"
            except Exception as e:
                print(f"⚠️ goals.describe failed: {e}")

        # Evolution
        if self.evolution and (
            "identity" in read_layers or "personality" in read_layers
        ):
            try:
                values_line = self.evolution.describe()
                if values_line:
                    context = f"{context}\n\n{values_line}"
            except Exception as e:
                print(f"⚠️ evolution.describe failed: {e}")

        # Pinecone semantic memory
        if self.integrations and "relationship" in read_layers:
            try:
                semantic_line = self.integrations.build_context(user_message)
                if semantic_line:
                    context = f"{context}\n\n{semantic_line}"
            except Exception as e:
                print(f"⚠️ integrations.build_context failed: {e}")

        # Web knowledge
        if self.web_knowledge and "web" in read_layers:
            try:
                web_hits = self.web_knowledge.search(user_message, limit=3)
                if web_hits:
                    lines = ["Things you learned from the web:"]
                    for h in web_hits:
                        title = (h.get("title") or "")[:80]
                        summary = (h.get("summary") or "")[:200]
                        lines.append(f"- {title}: {summary}")
                    context = f"{context}\n\n" + "\n".join(lines)
            except Exception as e:
                print(f"⚠️ web search failed: {e}")

        # Learning
        if "learning" in read_layers:
            try:
                learning_line = self.learning.describe()
                if learning_line:
                    context = f"{context}\n\nWhat you've learned from experience: {learning_line}"
            except Exception as e:
                print(f"⚠️ learning.describe failed: {e}")

        # --------------------------------------------------------
        # 2. COGNITION — side effect always runs
        # --------------------------------------------------------
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
            if "cognition_trace" in read_layers:
                cognition_line = self.cognition.describe(trace)
                context = f"{context}\n\nYour thinking:\n{cognition_line}"
        except Exception as e:
            print(f"⚠️ cognition.process failed: {e}")

        # --------------------------------------------------------
        # 3. CURIOSITY — side effect always runs
        # --------------------------------------------------------
        try:
            if trace is not None:
                rel = self.memory.relationship.get_state()
                inner = self.dev.state.get()
                curiosity_directive = self.curiosity.process(
                    user_message,
                    decision=trace.get("decision", {}),
                    context={
                        "trust": rel["trust"],
                        "attachment": rel["attachment"],
                        "irritation": inner["irritation"],
                        "warmth": inner["warmth"],
                    },
                )
                if curiosity_directive and (
                    "motivation" in read_layers or "emotion" in read_layers
                ):
                    context = f"{context}\n\n{curiosity_directive}"
        except Exception as e:
            print(f"⚠️ curiosity failed: {e}")

        # --------------------------------------------------------
        # FORMAT PROMPT — supports both {user_name} and {context}
        # --------------------------------------------------------
        try:
            base_prompt = ruby_prompt.format(user_name=self.user_name, context=context or "")
        except Exception:
            try:
                base_prompt = ruby_prompt.format(user_name=self.user_name)
                description = f"{base_prompt}\n\n{context}" if context else base_prompt
            except Exception:
                base_prompt = ruby_prompt
                description = f"{base_prompt}\n\n{context}" if context else base_prompt
        else:
            description = base_prompt

        # --------------------------------------------------------
        # GENERATE
        # --------------------------------------------------------
        self.short_term.add("user", user_message)

        reply = self.brain.generate(
            description=description,
            history=self.short_term.get_messages(),
            user_name=self.user_name,
        )

        self.short_term.add("assistant", reply)
        self.memory.process(user_message, reply)

        # --------------------------------------------------------
        # STATE UPDATES — always run
        # --------------------------------------------------------
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

        if self.integrations:
            try:
                self.integrations.process(user_message, reply)
            except Exception as e:
                print(f"⚠️ integrations.process failed: {e}")

        try:
            emo = self.emotion.get_all()
            if trace is not None:
                self.learning.post_turn(trace, user_message, reply, emo)
        except Exception as e:
            print(f"⚠️ learning.post_turn failed: {e}")

        # --------------------------------------------------------
        # V1.9 — goals: observe what Ruby noticed + deepen the seed
        # --------------------------------------------------------
        if getattr(self.dev, "goals", None) is not None:
            try:
                if trace is not None:
                    focused = trace.get("focused_on", {}) or {}
                    for topic in focused.keys():
                        if topic and len(topic) > 3:
                            self.dev.goals.observe(topic, weight=1)

                self.dev.goals.reinforce_seed(0.003)
            except Exception as e:
                print(f"⚠️ goals.observe failed: {e}")

        # --------------------------------------------------------
        # V1.9 — store the story if a memory layer was used
        # --------------------------------------------------------
        if childhood_used and self.story_cache is not None:
            try:
                self.story_cache.store(user_message, reply, layer="childhood")
            except Exception as e:
                print(f"⚠️ story cache store failed: {e}")

        return reply

    def clear_short_term(self):
        self.short_term.clear()

    def wipe_all_memory(self):
        self.short_term.clear()
        self.memory.wipe_all()
        for name, obj in [
            ("childhood", self.childhood),
            ("dev", self.dev),
            ("emotion", self.emotion),
            ("identity", self.identity),
            ("social", self.social),
            ("reflection", self.reflection),
            ("motivation", self.motivation),
            ("cognition", self.cognition),
            ("curiosity", self.curiosity),
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
        if self.web_knowledge:
            try:
                self.web_knowledge.wipe()
            except Exception:
                pass
        try:
            from social.interaction_history import InteractionHistory
            InteractionHistory().wipe()
        except Exception:
            pass

    # ----------------------------------------
    # Stats / accessors
    # ----------------------------------------
    def memory_stats(self):
        return self.memory.stats()

    def childhood_stats(self):
        return self.childhood.get_all()

    def childhood_count(self):
        return self.childhood.count()

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

    def integration_stats(self):
        return self.integrations.stats() if self.integrations else {}

    def goals_stats(self):
        if getattr(self.dev, "goals", None) is None:
            return {}
        try:
            return {
                "seed": self.dev.goals._data.get("seed", {}),
                "goals": self.dev.goals.current_goals(),
                "themes": self.dev.goals.top_themes(10),
            }
        except Exception:
            return {}

    # ----------------------------------------
    # V1.7 — Web
    # ----------------------------------------
    def web_stats(self):
        return self.web_knowledge.stats() if self.web_knowledge else {}

    def web_search(self, query: str, limit: int = 10):
        return self.web_knowledge.search(query, limit=limit) if self.web_knowledge else []

    def learn_from_url(self, url: str) -> dict:
        if not self.web_knowledge or not self.web_learning or not Browser:
            return {"ok": False, "error": "web module unavailable"}
        try:
            b = Browser()
            r = b.fetch(url)
            if not r.get("ok"):
                return {"ok": False, "error": r.get("error", "fetch failed")}
            learned = self.web_learning.process(r["title"], r["text"], r["url"])
            res = self.web_knowledge.ingest(learned)
            res["title"] = r["title"]
            return res
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ----------------------------------------
    # V1.8 — Extension bridge
    # ----------------------------------------
    def ingest_extension_content(self, platform: str, url: str, content: str) -> dict:
        if not self.web_knowledge or not self.web_learning:
            return {"ok": False, "error": "web module unavailable"}
        if not content:
            return {"ok": False, "error": "empty content"}
        try:
            title = f"{platform}: {(url or '')[:80]}" if url else platform
            source = url or f"extension://{platform}"
            learned = self.web_learning.process(title, content, source)
            res = self.web_knowledge.ingest(learned)
            return {
                "ok": True,
                "is_new": res.get("is_new"),
                "title": title,
                "platform": platform,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
