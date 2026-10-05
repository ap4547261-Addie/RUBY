# brain/response_engine.py
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

try:
    from brain.connectome import Connectome
    from brain.global_workspace import GlobalWorkspace
    BLUEPRINT_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Blueprint modules not available: {e}")
    BLUEPRINT_AVAILABLE = False
    Connectome = None
    GlobalWorkspace = None

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

try:
    from evolution.development_engine import DevelopmentEngine
    EVOLUTION_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Evolution layer not available: {e}")
    EVOLUTION_AVAILABLE = False
    DevelopmentEngine = None

try:
    from integrations.integration_engine import IntegrationEngine
    INTEGRATIONS_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Integrations layer not available: {e}")
    INTEGRATIONS_AVAILABLE = False
    IntegrationEngine = None

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
    def __init__(self, brain, user_name="not_set", platform="private", curiosity=None):
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
        self.curiosity = curiosity if curiosity is not None else Curiosity()
        self.learning = LearningEngine(user_name=user_name)
        self.personality = PersonalityDevelopment(user_name=user_name)

        if BLUEPRINT_AVAILABLE:
            self.connectome = Connectome()
            self.workspace = GlobalWorkspace()
        else:
            self.connectome = None
            self.workspace = None

        if EVOLUTION_AVAILABLE:
            try:
                self.evolution = DevelopmentEngine(user_name=user_name)
            except Exception as e:
                print(f"⚠️ Evolution init failed: {e}")
                self.evolution = None
        else:
            self.evolution = None

        if INTEGRATIONS_AVAILABLE:
            try:
                self.integrations = IntegrationEngine(user_name=user_name)
            except Exception as e:
                print(f"⚠️ Integrations init failed: {e}")
                self.integrations = None
        else:
            self.integrations = None

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

    def respond_fast(self, user_message: str, ruby_prompt: str) -> str:
        if "{context}" in ruby_prompt:
            try:
                description = ruby_prompt.format(user_name=self.user_name, context="")
            except Exception:
                description = ruby_prompt
        else:
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

    def respond(self, user_message: str, ruby_prompt: str) -> str:
        if self.connectome and self.workspace:
            self.workspace.clear()
            self.connectome.update_node("thalamus", 0.9)

        try:
            self.curiosity.notice(user_message)
        except Exception as e:
            print(f"⚠️ curiosity.notice failed: {e}")

        try:
            self.learning.pre_turn(user_message)
        except Exception as e:
            print(f"⚠️ learning.pre_turn failed: {e}")

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

        context = ""

        if "episodic" in read_layers or "relationship" in read_layers:
            try:
                mem_ctx = self.memory.build_context(user_message)
                if mem_ctx:
                    context = f"{context}\n\n{mem_ctx}"
                    if self.workspace: self.workspace.broadcast("memory", mem_ctx)
            except Exception as e:
                print(f"⚠️ memory.build_context failed: {e}")

        if "childhood" in read_layers:
            try:
                childhood_line = self.childhood.build_context(user_message, limit=None)
                if childhood_line:
                    context = f"{context}\n\n{childhood_line}"
                    if self.workspace: self.workspace.broadcast("childhood", childhood_line)
            except Exception as e:
                print(f"⚠️ childhood.build_context failed: {e}")

        try:
            inner_line = self.dev.describe()
            context = f"{context}\n\nYour body and mood: {inner_line}"
            if self.workspace: self.workspace.broadcast("internal_state", inner_line)
        except Exception as e:
            print(f"⚠️ dev.describe failed: {e}")

        if "emotion" in read_layers:
            try:
                emotions = self.emotion.get_all()
                emotion_line = self.emotion_expr.describe(emotions)
                context = f"{context}\n\nYour feelings right now: {emotion_line}"
                if self.workspace: self.workspace.broadcast("emotion", emotion_line)
                if self.connectome: self.connectome.update_node("amygdala", 0.7)
            except Exception as e:
                print(f"⚠️ emotion.describe failed: {e}")

        if "identity" in read_layers:
            try:
                identity_line = self.identity.describe()
                context = f"{context}\n\n{identity_line}"
                if self.workspace: self.workspace.broadcast("identity", identity_line)
            except Exception as e:
                print(f"⚠️ identity.describe failed: {e}")

        if "social" in read_layers:
            try:
                social_line = self.social.describe()
                context = f"{context}\n\nWho he is to you:\n{social_line}"
                if self.workspace: self.workspace.broadcast("social", social_line)
            except Exception as e:
                print(f"⚠️ social.describe failed: {e}")

        if "motivation" in read_layers:
            try:
                drive_line = self.motivation.describe()
                context = f"{context}\n\nWhat you need right now: {drive_line}"
                if self.workspace: self.workspace.broadcast("motivation", drive_line)
            except Exception as e:
                print(f"⚠️ motivation.describe failed: {e}")

        if "personality" in read_layers:
            try:
                personality_line = self.personality.describe()
                context = f"{context}\n\n{personality_line}"
                if self.workspace: self.workspace.broadcast("personality", personality_line)
            except Exception as e:
                print(f"⚠️ personality.describe failed: {e}")

        if ("motivation" in read_layers or "identity" in read_layers) and getattr(self.dev, "goals", None) is not None:
            try:
                goals_line = self.dev.goals.describe()
                if goals_line:
                    context = f"{context}\n\n{goals_line}"
                    if self.workspace: self.workspace.broadcast("goals", goals_line)
            except Exception as e:
                print(f"⚠️ goals.describe failed: {e}")

        if self.evolution and ("identity" in read_layers or "personality" in read_layers):
            try:
                values_line = self.evolution.describe()
                if values_line:
                    context = f"{context}\n\n{values_line}"
                    if self.workspace: self.workspace.broadcast("evolution", values_line)
            except Exception as e:
                print(f"⚠️ evolution.describe failed: {e}")

        if self.integrations and "relationship" in read_layers:
            try:
                semantic_line = self.integrations.build_context(user_message)
                if semantic_line:
                    context = f"{context}\n\n{semantic_line}"
                    if self.workspace: self.workspace.broadcast("integrations", semantic_line)
            except Exception as e:
                print(f"⚠️ integrations.build_context failed: {e}")

        if self.web_knowledge and "web" in read_layers:
            try:
                web_hits = self.web_knowledge.search(user_message, limit=3)
                if web_hits:
                    lines = ["Things you learned from the web:"]
                    for h in web_hits:
                        title = (h.get("title") or "")[:80]
                        summary = (h.get("summary") or "")[:200]
                        lines.append(f"- {title}: {summary}")
                    web_line = "\n".join(lines)
                    context = f"{context}\n\n{web_line}"
                    if self.workspace: self.workspace.broadcast("web", web_line)
            except Exception as e:
                print(f"⚠️ web search failed: {e}")

        if "learning" in read_layers:
            try:
                learning_line = self.learning.describe()
                if learning_line:
                    context = f"{context}\n\nWhat you've learned from experience: {learning_line}"
                    if self.workspace: self.workspace.broadcast("learning", learning_line)
            except Exception as e:
                print(f"⚠️ learning.describe failed: {e}")

        curiosity_instruction = ""
        try:
            if self.curiosity.should_ask():
                ctx = self.curiosity.get_ask_context()
                if ctx:
                    curiosity_instruction = (
                        f"Trigger: {ctx['subject']}\n"
                        f"Reason: {ctx['reason']}\n"
                        f"Instruction: {ctx['instruction']}"
                    )
                    self.curiosity.mark_explored(ctx['subject'], ctx['category'])
                    print(f"🔍 Curiosity Triggered inside Engine: {ctx['subject']}")
                    if self.workspace: self.workspace.broadcast("curiosity", curiosity_instruction)
        except Exception as e:
            print(f"⚠️ curiosity context generation failed: {e}")

        try:
            strong = self.curiosity.strongest()
            if strong and strong.get("strength", 0) >= 0.55:
                lines = ["Things you've been noticing you don't fully understand:"]
                lines.append(f"- {strong['subject']} ({strong['reason']})")
                for u in self.curiosity.peek_unknowns()[:2]:
                    if u.get("strength", 0) >= 0.55 and u["subject"] != strong["subject"]:
                        lines.append(f"- {u['subject']}")
                context = f"{context}\n\n" + "\n".join(lines)
        except Exception as e:
            print(f"⚠️ curiosity context failed: {e}")

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
                if self.workspace: self.workspace.broadcast("cognition_trace", cognition_line)
        except Exception as e:
            print(f"⚠️ cognition.process failed: {e}")

        if self.workspace:
            workspace_context = self.workspace.build_prompt_context()
            if workspace_context:
                context = f"{context}\n\n--- GLOBAL WORKSPACE ---\n{workspace_context}"
            self.connectome.update_node("global_workspace", 0.95)

        # 🔥 SAFETY: Cap context so the model doesn't overflow
        MAX_CONTEXT_CHARS = 6000
        if len(context) > MAX_CONTEXT_CHARS:
            print(f"⚠️ Context too big ({len(context)} chars), trimming to {MAX_CONTEXT_CHARS}")
            context = context[:MAX_CONTEXT_CHARS] + "\n[...truncated...]"

        if "{context}" in ruby_prompt:
            try:
                description = ruby_prompt.format(user_name=self.user_name, context=context or "")
            except Exception:
                description = f"{ruby_prompt}\n\nWhat you know right now:\n{context}"
        else:
            description = f"{ruby_prompt}\n\nWhat you know right now:\n{context}"

        if curiosity_instruction and "CURIOSITY ENGINE INSTRUCTION" not in description:
            description += f"\n\nCURIOSITY ENGINE INSTRUCTION:\n{curiosity_instruction}"

        self.short_term.add("user", user_message)
        if self.connectome: self.connectome.update_node("decision", 1.0)

        print(f"🔍 PROMPT LEN: {len(description)} chars (~{len(description)//4} tokens)")
        print(f"🔍 HAS CAMERA TOOL: {'CAMERA TOOL' in description}")
        print(f"🔍 HAS SEND_SELFIE: {'SEND_SELFIE' in description}")

        try:
            reply = self.brain.generate(
                description=description,
                history=self.short_term.get_messages(),
                user_name=self.user_name,
            )
        except Exception as e:
            print(f"⚠️ brain.generate failed: {e}")
            reply = "[GENERATION ERROR] " + str(e)

        self.short_term.add("assistant", reply)
        self.memory.process(user_message, reply)

        try:
            self.dev.tick()
            rel = self.memory.relationship.get_state()
            self.dev.on_message(user_message, reply, trust=rel["trust"], attachment=rel["attachment"])
        except Exception as e:
            print(f"⚠️ dev.on_message failed: {e}")

        try:
            rel = self.memory.relationship.get_state()
            inner = self.dev.state.get()
            self.emotion.process(user_message, context={
                "trust": rel["trust"], "attachment": rel["attachment"],
                "warmth": inner["warmth"], "irritation": inner["irritation"],
                "message_count": rel["message_count"],
            })
        except Exception as e:
            print(f"⚠️ emotion.process failed: {e}")

        try:
            rel = self.memory.relationship.get_state()
            emo = self.emotion.get_all()
            inner = self.dev.state.get()
            self.identity.process(user_message, reply, context={
                "trust": rel["trust"], "attachment": rel["attachment"], "emotions": emo,
                "irritation": inner["irritation"], "warmth": inner["warmth"],
            })
        except Exception as e:
            print(f"⚠️ identity.process failed: {e}")

        try:
            rel = self.memory.relationship.get_state()
            emo = self.emotion.get_all()
            inner = self.dev.state.get()
            self.social.process(user_message, reply, context={
                "trust": rel["trust"], "attachment": rel["attachment"],
                "emotions": emo, "internal_state": inner,
            })
        except Exception as e:
            print(f"⚠️ social.process failed: {e}")

        try:
            rel = self.memory.relationship.get_state()
            emo = self.emotion.get_all()
            inner = self.dev.state.get()
            self.reflection.process(
                internal_state=inner, emotions=emo,
                beliefs=self.identity.beliefs(),
                message_count=rel["message_count"],
            )
        except Exception as e:
            print(f"⚠️ reflection.process failed: {e}")

        try:
            rel = self.memory.relationship.get_state()
            emo = self.emotion.get_all()
            inner = self.dev.state.get()
            self.motivation.process(user_message, context={
                "trust": rel["trust"], "attachment": rel["attachment"],
                "emotions": emo, "internal_state": inner,
            })
        except Exception as e:
            print(f"⚠️ motivation.process failed: {e}")

        try:
            rel = self.memory.relationship.get_state()
            emo = self.emotion.get_all()
            inner = self.dev.state.get()
            self.personality.process(
                internal_state=inner, emotions=emo,
                relationship=rel, learning=None,
            )
        except Exception as e:
            print(f"⚠️ personality.process failed: {e}")

        if self.evolution:
            try:
                rel = self.memory.relationship.get_state()
                emo = self.emotion.get_all()
                inner = self.dev.state.get()
                self.evolution.process(
                    internal_state=inner, emotions=emo,
                    relationship=rel, learning=None,
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

        if self.connectome:
            self.connectome.propagate()

        return reply

    def get_brain_state(self):
        if not self.connectome:
            return {}
        return self.connectome.nodes

    def clear_short_term(self):
        self.short_term.clear()

    def wipe_all_memory(self):
        self.short_term.clear()
        self.memory.wipe_all()
        if self.connectome: self.connectome = Connectome()
        if self.workspace: self.workspace.clear()

        for name, obj in [
            ("childhood", self.childhood), ("dev", self.dev), ("emotion", self.emotion),
            ("identity", self.identity), ("social", self.social), ("reflection", self.reflection),
            ("motivation", self.motivation), ("cognition", self.cognition),
            ("curiosity", self.curiosity), ("learning", self.learning),
            ("personality", self.personality),
        ]:
            try:
                obj.wipe()
            except Exception:
                pass
        if self.evolution:
            try: self.evolution.wipe()
            except Exception: pass
        if self.integrations:
            try: self.integrations.wipe()
            except Exception: pass
        if self.web_knowledge:
            try: self.web_knowledge.wipe()
            except Exception: pass
        try:
            from social.interaction_history import InteractionHistory
            InteractionHistory().wipe()
        except Exception:
            pass

    # --- Stats / accessors ---
    def memory_stats(self): return self.memory.stats()
    def childhood_stats(self): return self.childhood.get_all()
    def childhood_count(self): return self.childhood.count()
    def emotion_stats(self): return self.emotion.get_all()
    def internal_state_stats(self): return self.dev.state.get()
    def identity_stats(self): return self.identity.beliefs()
    def identity_history(self): return self.identity.history_recent(limit=40)
    def social_stats(self): return self.social.model.get()
    def reflection_stats(self): return self.reflection.counts()
    def reflections_recent(self, limit=None): return self.reflection.recent_reflections(limit=limit)
    def experience_reviews_recent(self, limit=None): return self.reflection.recent_experience_reviews(limit=limit)
    def long_term_reflections_recent(self, limit=None): return self.reflection.recent_long_term(limit=limit)
    def drives_stats(self): return self.motivation.get_all()
    def cognition_trace(self): return self.cognition.last_trace()
    def learning_summary(self): return self.learning.error_summary()
    def recent_prediction_errors(self, limit=10): return self.learning.recent_errors(limit=limit)
    def preference_stats(self): return self.learning.preferences()
    def best_behaviors(self, limit=5): return self.learning.best_behaviors(limit=limit)
    def worst_behaviors(self, limit=5): return self.learning.worst_behaviors(limit=limit)
    def personality_stats(self): return self.personality.traits()
    def values_stats(self): return self.evolution.get_values() if self.evolution else {}
    def value_history(self, limit=None): return self.evolution.get_value_history(limit=limit) if self.evolution else []
    def evolution_personality(self): return self.evolution.get_personality() if self.evolution else {}
    def evolution_preferences(self): return self.evolution.get_preferences() if self.evolution else []
    def integration_stats(self): return self.integrations.stats() if self.integrations else {}

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

    def curiosity_stats(self):
        try:
            return {
                "interests": self.curiosity.peek_interests(),
                "unknowns": self.curiosity.peek_unknowns(),
                "uncertainties": self.curiosity.peek_uncertainties(),
                "strongest": self.curiosity.strongest(),
            }
        except Exception:
            return {}

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
            return {"ok": True, "is_new": res.get("is_new"), "title": title, "platform": platform}
        except Exception as e:
            return {"ok": False, "error": str(e)}
