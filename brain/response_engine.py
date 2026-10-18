# brain/response_engine.py
import os
from datetime import datetime, timedelta
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
from brain.time_awareness import time_context
from ruby_core.circadian import effective_energy

try:
    from learning.style_learning import StyleLearning
except Exception as e:
    print(f"⚠️ StyleLearning not available: {e}")
    StyleLearning = None

try:
    from brain.proactive import ProactiveEngine
except Exception as e:
    print(f"⚠️ ProactiveEngine not available: {e}")
    ProactiveEngine = None

try:
    from memory.sleep import SleepCycle
except Exception as e:
    print(f"⚠️ SleepCycle not available: {e}")
    SleepCycle = None

try:
    from brain.idle_thoughts import IdleThoughts
except Exception as e:
    print(f"⚠️ IdleThoughts not available: {e}")
    IdleThoughts = None

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

        # Learns which of her own moves (tease, warmth, question...) land.
        self._reply_seq = 0           # bumped each time a reply is stored
        self._style_scored_seq = 0    # last reply already scored
        self.style = None
        if StyleLearning is not None:
            try:
                self.style = StyleLearning(user_name=user_name)
            except Exception as e:
                print(f"⚠️ StyleLearning init failed: {e}")

        # Decides when Ruby texts first (see brain/proactive.py)
        self.proactive = None
        self._last_proactive_attempt = None
        if ProactiveEngine is not None:
            try:
                self.proactive = ProactiveEngine(user_name=user_name)
            except Exception as e:
                print(f"⚠️ ProactiveEngine init failed: {e}")

        # Sleep (memory consolidation) and idle thoughts (her mind between messages)
        self.sleep = None
        self.idle = None
        if SleepCycle is not None:
            try:
                self.sleep = SleepCycle(user_name=user_name)
            except Exception as e:
                print(f"⚠️ SleepCycle init failed: {e}")
        if IdleThoughts is not None:
            try:
                self.idle = IdleThoughts(user_name=user_name)
            except Exception as e:
                print(f"⚠️ IdleThoughts init failed: {e}")

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

    # ------------------------------------------------------------
    # Small helpers shared by respond() and respond_fast()
    # ------------------------------------------------------------
    @staticmethod
    def _is_error_reply(reply: str) -> bool:
        """Replies produced by failures — never learn from or store these."""
        r = (reply or "").strip()
        return (not r) or r.startswith((
            "[GEN ERROR]", "[GENERATION ERROR]", "[FAST ERROR]",
            "My brain isn't loaded",
        ))

    @staticmethod
    def _trim_block(text: str, limit: int) -> str:
        """Shorten one context block, ending on a sentence boundary when possible."""
        if len(text) <= limit:
            return text
        cut = text[:limit]
        idx = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "), cut.rfind("\n"))
        if idx > limit * 0.5:
            cut = cut[:idx + 1]
        return cut.rstrip()

    def _mood_label(self) -> str:
        """Coarse mood used to key style learning (few buckets, so it learns fast)."""
        try:
            s = self.dev.state.get()
            if s["irritation"] > 0.5:
                return "irritated"
            if effective_energy(s["energy"]) < 0.33:
                return "tired"
            if s["warmth"] > 0.7:
                return "warm"
            if s["warmth"] < 0.3:
                return "distant"
        except Exception:
            pass
        return "neutral"

    def _time_line(self) -> str:
        """Clock + gap since the previous exchange. Call BEFORE memory.process()."""
        try:
            # the gap is measured from the USER's last message (not from a text Ruby sent first)
            return time_context(self.memory.episodic.last_user_timestamp())
        except Exception as e:
            print(f"⚠️ time_context failed: {e}")
            return ""

    def _observe_style(self, user_message: str):
        """Score how the user reacted to Ruby's previous reply."""
        if self.style is None:
            return
        # Score each reply only once, even if the user's next message fails
        # and they retry (otherwise the same reply is counted twice).
        if self._reply_seq == self._style_scored_seq:
            return
        self._style_scored_seq = self._reply_seq
        try:
            prev = None
            for m in reversed(self.short_term.get_messages()):
                if m["role"] == "assistant":
                    prev = m["content"]
                    break
            if prev and not self._is_error_reply(prev):
                self.style.observe(self._mood_label(), "", prev, user_message)
        except Exception as e:
            print(f"⚠️ style.observe failed: {e}")

    def _style_context(self) -> str:
        if self.style is None:
            return ""
        try:
            mood = self._mood_label()
            text = self.style.describe(mood)
            if not text:
                return ""
            best = self.style.best_moves(mood, 1)
            if best:
                for ex in self.style.recent_landed(best[0]["move"], 2):
                    said = (ex.get("said") or "")[:120]
                    if said:
                        text += f'\nA line of yours that landed before: "{said}"'
            return "What has landed with them before:\n" + text
        except Exception as e:
            print(f"⚠️ style context failed: {e}")
            return ""

    def _update_after_reply(self, user_message: str, reply: str):
        """Cheap state updates that must happen for EVERY turn, fast or full."""
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

    # ------------------------------------------------------------
    # Her mind between messages: sleep, idle thoughts, emotional echoes
    # ------------------------------------------------------------
    def tend_mind(self, now=None):
        """
        Background upkeep, no model calls (cheap, call about once a minute):
        consolidate memory if a night has passed, and let a new idle thought form.
        """
        now = now or datetime.now()
        if self.sleep is not None:
            try:
                self.sleep.maybe_sleep(now)
            except Exception as e:
                print(f"⚠️ sleep failed: {e}")
        if self.idle is not None:
            try:
                sources = {}
                gist = self.sleep.gist() if self.sleep is not None else None
                if gist:
                    sources["gist"] = gist
                try:
                    ep = self.memory.episodic.recent_emotional(now=now)
                    if ep:
                        sources["recent_emotional"] = ep
                except Exception:
                    pass
                try:
                    unknowns = self.curiosity.peek_unknowns()
                    if unknowns:
                        best = max(unknowns, key=lambda u: u.get("strength", 0))
                        sources["unknown"] = best.get("subject")
                    interests = self.curiosity.peek_interests()
                    if interests:
                        best = max(interests, key=lambda u: u.get("strength", 0))
                        sources["interest"] = f"The subject of {best.get('subject')}"
                except Exception:
                    pass
                made = self.idle.think(now, sources, display=self.memory._display_name())
                if made and made["kind"] == "gist" and self.sleep is not None:
                    self.sleep.clear_gist()
            except Exception as e:
                print(f"⚠️ idle thought failed: {e}")

    def _idle_context(self, user_message: str) -> str:
        """Sometimes, in a quiet moment, a thought slips out. Returns a context line or ''."""
        if self.idle is None:
            return ""
        try:
            t = self.idle.maybe_for_chat(user_message)
            if not t:
                return ""
            self.idle.mark_surfaced(t["id"])
            return ("Something has been on your mind (bring it up only if it fits the moment, "
                    "in your own words — don't recite it, and drop it if they're busy with "
                    f"something else): {t['seed']}")
        except Exception as e:
            print(f"⚠️ idle context failed: {e}")
            return ""

    def _echo_mood(self):
        """A vivid memory she just recalled colours how she feels right now (a little)."""
        recall = getattr(self.memory, "last_recall", None)
        self.memory.last_recall = None
        if not recall:
            return
        try:
            emo = recall["emotion"]
            name = "warmth" if emo == "closeness" else emo
            amount = 0.08 * float(recall["intensity"])
            self.emotion.state.add_many({name: amount})
        except Exception as e:
            print(f"⚠️ emotional echo failed: {e}")

    def respond_fast(self, user_message: str, ruby_prompt: str) -> str:
        """
        Fast path for greetings / one-word messages.

        Used to run with NO context, so "hey" got the same reply from a
        stranger and from someone she's attached to, and nothing was saved.
        Now it gets a LIGHT context (hour, gap, relationship tone, body,
        feelings) and still updates her memory and mood — but skips the
        expensive layers (web, childhood, identity, cognition...).
        """
        self._observe_style(user_message)

        parts = []
        try:
            t = self._time_line()
            if t:
                parts.append(t)
        except Exception:
            pass
        try:
            # empty message -> no keyword episode search, just facts + relationship tone
            rel_ctx = self.memory.build_context("")
            if rel_ctx:
                parts.append(rel_ctx)
        except Exception as e:
            print(f"⚠️ fast memory context failed: {e}")
        try:
            parts.append(f"Your body and mood: {self.dev.describe()}")
            parts.append(f"Your feelings right now: {self.emotion_expr.describe(self.emotion.get_all())}")
        except Exception as e:
            print(f"⚠️ fast mood context failed: {e}")
        try:
            style_ctx = self._style_context()
            if style_ctx:
                parts.append(style_ctx)
        except Exception:
            pass
        idle_line = self._idle_context(user_message)
        if idle_line:
            parts.append(idle_line)

        context = "\n\n".join(p for p in parts if p)

        if "{context}" in ruby_prompt:
            try:
                description = ruby_prompt.format(user_name=self.user_name, context=context)
            except Exception:
                description = f"{ruby_prompt}\n\nWhat you know right now:\n{context}"
        else:
            description = f"{ruby_prompt}\n\nWhat you know right now:\n{context}" if context else ruby_prompt

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

        if self._is_error_reply(reply):
            # don't let errors pollute history, memory or style stats
            self.short_term.discard_last()
            return reply

        self.short_term.add("assistant", reply)
        self._reply_seq += 1
        try:
            self.memory.process(user_message, reply)
        except Exception as e:
            print(f"⚠️ fast memory.process failed: {e}")
        self._update_after_reply(user_message, reply)
        return reply

    # ------------------------------------------------------------
    # Ruby texting FIRST
    # ------------------------------------------------------------
    def plan_proactive(self, enabled: bool = True):
        """
        Cheap check (a few SQLite reads) — safe to call once a minute.
        Returns a plan dict {"reason", "instruction", "idle_hours"} or None.
        """
        if self.proactive is None or not enabled:
            return None
        try:
            now = datetime.now()
            # after a failed/duplicate attempt, don't hammer the model every minute
            retry = timedelta(minutes=1 if os.environ.get("RUBY_PROACTIVE_DEBUG") == "1" else 10)
            if self._last_proactive_attempt and now - self._last_proactive_attempt < retry:
                return None
            ts = self.memory.episodic.last_user_timestamp()
            last = datetime.fromisoformat(ts) if ts else None
            rel = self.memory.relationship.get_state()
            return self.proactive.decide(now, last, rel, self._mood_label(), enabled=True)
        except Exception as e:
            print(f"⚠️ plan_proactive failed: {e}")
            return None

    def respond_proactive(self, ruby_prompt: str, plan: dict):
        """
        Ruby starts the conversation. Returns her text, or None if nothing
        should be sent (error, or she'd be repeating herself).
        Nothing is written as a "user message": the text is stored with an
        empty user_message so it can't distort relationship stats.
        """
        self._last_proactive_attempt = datetime.now()

        parts = []
        try:
            t = self._time_line()
            if t:
                parts.append(t)
        except Exception:
            pass
        try:
            rel_ctx = self.memory.build_context("")
            if rel_ctx:
                parts.append(rel_ctx)
        except Exception as e:
            print(f"⚠️ proactive memory context failed: {e}")
        try:
            parts.append(f"Your body and mood: {self.dev.describe()}")
            parts.append(f"Your feelings right now: {self.emotion_expr.describe(self.emotion.get_all())}")
        except Exception as e:
            print(f"⚠️ proactive mood context failed: {e}")
        try:
            rows = self.memory.episodic.get_recent(limit=3)
            lines = []
            for u, r, _ts in reversed(rows):
                if u:
                    lines.append(f'- they said: "{u[:90]}" / you said: "{r[:90]}"')
            if lines:
                parts.append("The last things you two talked about:\n" + "\n".join(lines))
        except Exception:
            pass
        try:
            style_ctx = self._style_context()
            if style_ctx:
                parts.append(style_ctx)
        except Exception:
            pass

        # Something on her mind is the natural reason to text. Not when she's
        # stung (ignored) and not when she's pretending she didn't notice (missing).
        thought = None
        if self.idle is not None and plan.get("reason") in ("random_thought", "late_night"):
            try:
                thought = self.idle.peek()
            except Exception:
                thought = None
        thought_line = ""
        if thought:
            thought_line = (f" This is what's on your mind, and why you're texting: {thought['seed']} "
                            f"Say it in your own words, the way you'd text it — don't quote this.")

        context = "\n\n".join(p for p in parts if p)
        description = (
            f"{ruby_prompt}\n\nWhat you know right now:\n{context}\n\n"
            f"YOU ARE TEXTING FIRST — they did not write to you. {plan.get('instruction', '')}"
            f"{thought_line} Never mention that you were told or prompted to do this."
        )

        # the model needs a final user turn; this stand-in is NOT stored anywhere
        history = self.short_term.get_messages() + [
            {"role": "user", "content": "(They haven't written. You decide to text them first.)"}
        ]
        try:
            reply = self.brain.generate(
                description=description, history=history, user_name=self.user_name,
            )
        except Exception as e:
            print(f"⚠️ respond_proactive failed: {e}")
            return None

        if self._is_error_reply(reply):
            return None

        # never say the same thing twice in a row
        seen = {m["content"].strip().lower() for m in self.short_term.get_messages()
                if m["role"] == "assistant"}
        try:
            seen |= {r.strip().lower() for _u, r, _t in self.memory.episodic.get_recent(limit=5)}
        except Exception:
            pass
        if reply.strip().lower() in seen:
            print("ℹ️ proactive text was a repeat — dropped")
            return None

        self.short_term.add("assistant", reply)
        self._reply_seq += 1
        try:
            self.memory.episodic.remember("", reply, importance=2)
        except Exception as e:
            print(f"⚠️ proactive episode save failed: {e}")
        if self.proactive is not None:
            self.proactive.record_sent()
        if thought and self.idle is not None:
            self.idle.mark_surfaced(thought["id"])
        print(f"💌 Ruby texted first ({plan.get('reason')})")
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

        # Score how they reacted to her last reply, then learn from it.
        self._observe_style(user_message)

        # Time comes first: it's short, and it's the first thing a person notices.
        context = self._time_line()

        if "episodic" in read_layers or "relationship" in read_layers:
            try:
                mem_ctx = self.memory.build_context(user_message)
                self._echo_mood()
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

        idle_line = self._idle_context(user_message)
        if idle_line:
            context = f"{context}\n\n{idle_line}"

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

        style_ctx = self._style_context()
        if style_ctx:
            context = f"{context}\n\n{style_ctx}"
            if self.workspace: self.workspace.broadcast("style", style_ctx)

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

        # NOTE: the workspace used to be appended here too, which put every
        # layer in the prompt twice and then cut off the end. Every layer is
        # already in `context`; the workspace is only kept for the brain monitor.
        if self.workspace:
            self.connectome.update_node("global_workspace", 0.95)

        # SAFETY: cap context so the model doesn't overflow. Trim whole
        # blocks (never mid-sentence); a block that doesn't fit is skipped
        # so shorter, later blocks can still make it in.
        MAX_CONTEXT_CHARS = 3500
        MAX_BLOCK_CHARS = 1200   # one huge layer (e.g. all 90 beliefs) must not crowd out the rest
        if len(context) > MAX_CONTEXT_CHARS:
            blocks = [self._trim_block(b.strip(), MAX_BLOCK_CHARS)
                      for b in context.split("\n\n") if b.strip()]
            kept, used = [], 0
            for b in blocks:
                if used + len(b) + 2 <= MAX_CONTEXT_CHARS or not kept:
                    kept.append(b)
                    used += len(b) + 2
            print(f"⚠️ Context too big ({len(context)} chars), kept {len(kept)}/{len(blocks)} blocks")
            context = "\n\n".join(kept)

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

        if self._is_error_reply(reply):
            # failed generation: don't store it, learn from it, or show it to the model next turn
            self.short_term.discard_last()
            return reply

        self.short_term.add("assistant", reply)
        self._reply_seq += 1
        self.memory.process(user_message, reply)
        self._update_after_reply(user_message, reply)

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
        if self.proactive:
            try: self.proactive.wipe()
            except Exception: pass
        for obj in (self.sleep, self.idle):
            if obj:
                try: obj.wipe()
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
