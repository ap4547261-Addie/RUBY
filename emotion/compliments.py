# emotion/compliments.py — recognising compliments.
# Pure keyword rules, no LLM. Compliments make Ruby genuinely happy (people
# used to call her weird for her hair and skin), and compliments about her
# LOOKS or about being a model hit hardest.

from typing import Optional

LOOKS = (
    "you're pretty", "you are pretty", "you look pretty", "so pretty",
    "you're beautiful", "you are beautiful", "you look beautiful", "so beautiful",
    "you're gorgeous", "you are gorgeous", "gorgeous", "you're stunning", "you are stunning",
    "you're cute", "you are cute", "you look cute",
    "you look amazing", "you look so good", "you look good", "you look great",
    "love your hair", "like your hair", "beautiful hair", "your hair looks", "your hair is beautiful",
    "love your freckles", "cute freckles", "beautiful freckles",
    "love your skin", "beautiful skin", "glowing skin", "love your eyes", "beautiful eyes",
)

MODEL = (
    "should be a model", "could be a model", "be a model", "model material",
    "you could model", "great model", "supermodel",
)

GENERAL = (
    "you're smart", "you are smart", "you're amazing", "you are amazing",
    "you're talented", "you are talented", "you're brilliant", "you're incredible",
    "you're awesome", "you are awesome", "you're wonderful", "you are wonderful",
    "you're special", "i admire you", "i'm proud of you",
)

# Cheap guard so "i don't think you're beautiful" isn't read as a compliment.
_NEGATIONS = (" not ", "n't", "never", "nobody", "no one", "ugly", "hate")


def compliment_kind(text: str) -> Optional[str]:
    """Return "model", "looks", "general", or None."""
    t = f" {(text or '').lower()} "
    if any(n in t for n in _NEGATIONS):
        return None
    if any(p in t for p in MODEL):
        return "model"
    if any(p in t for p in LOOKS):
        return "looks"
    if any(p in t for p in GENERAL):
        return "general"
    return None
