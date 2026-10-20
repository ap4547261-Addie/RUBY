# brain/scene_from_reply.py — turn what Ruby SAID she's doing into a scene.
#
# The picture is built from her reply, not the other way round: if she texts
# "lying on my bed, bored" the photo shows her on a bed looking bored; if she
# says "at a coffee shop with a latte" it shows a coffee shop. No LLM call —
# plain rules, instant, so it can run on every reply.
#
#   extract_scene("ugh, lying on my bed in pajamas. bored.")
#       -> {"place": "in her cozy bedroom", "pose": "lying on her bed",
#           "outfit": "cozy pajamas", "mood": "bored"}
#
# is_status_question(user_message) says whether the user asked what/where she is
# or asked for a picture — the cue to actually make a photo.
#
# Only PRESENT, first-person statements count ("i'm at the park", "sitting in a
# cafe"). Questions, negations, the past ("i was at the park") and the future
# ("going to the gym later") are ignored, so a photo never contradicts her words.

import re
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------- questions
_STATUS_PATTERNS = [
    r"\bwhat\s*(?:'?s|is|are|r)?\s*(?:you|u|ya)\s*(?:doing|up\s*to|upto|been\s*doing)\b",
    r"\bwhat\s+are\s+you\s+up\s+to\b",
    r"\bwh?at\s*(?:'?cha|cha)\s*doing\b",
    r"\bwyd\b",
    r"\bwhere\s*(?:are|r|'?re)\s*(?:you|u)\b(?!\s*(?:from|going|headed))",
    r"\bwhere\s+you\s+at\b",
    r"\bwhat\s*(?:are|r)\s*(?:you|u)\s*wearing\b",
    r"\bhow\s+do\s+you\s+look\b",
    r"\b(?:show|send|share|give)\b.{0,25}\b(?:pic|picture|photo|selfie|image)\b",
    r"\b(?:pic|picture|photo|selfie|image)\s+of\s+(?:you|u|yourself)\b",
    r"\b(?:let\s+me|can\s+i)\s+see\s+(?:you|u)\b",
    r"\bshow\s+me\s+(?:where\s+you|what\s+you|you\b|yourself)",
]
_STATUS_RE = [re.compile(p, re.I) for p in _STATUS_PATTERNS]


def is_status_question(user_message: str) -> bool:
    t = (user_message or "").strip().lower()
    return bool(t) and any(r.search(t) for r in _STATUS_RE)


# ---------------------------------------------------------------- places
# (regex, place text for the image model, default pose or "")
_PLACES: List[Tuple[str, str, str]] = [
    (r"\b(coffee\s*shop|coffeeshop|cafe|café|starbucks|coffee place)\b", "in a cozy coffee shop", "sitting"),
    (r"\b(library)\b", "in a quiet library among bookshelves", "sitting"),
    (r"\b(book\s*store|bookstore|bookshop)\b", "in a cozy bookstore", "standing"),
    (r"\b(park|garden|lawn|bench)\b", "in a sunny green park", ""),
    (r"\b(beach|seaside|shore)\b", "on a sunny beach", ""),
    (r"\b(rooftop|roof)\b", "on a rooftop at golden hour", ""),
    (r"\b(balcony|terrace|veranda)\b", "on a balcony in warm evening light", ""),
    (r"\b(gym)\b", "in a gym", "standing"),
    (r"\b(college|campus|classroom|class|lecture)\b", "on a college campus", ""),
    (r"\b(mall|shopping|supermarket|store)\b", "in a shopping mall", "standing"),
    (r"\b(restaurant|diner|canteen|dhaba)\b", "in a restaurant", "sitting"),
    (r"\b(kitchen)\b", "in a kitchen", "standing"),
    (r"\b(bathroom|mirror)\b", "in front of a mirror", "standing"),
    (r"\b(museum|gallery)\b", "in an art gallery", "standing"),
    (r"\b(cinema|theater|theatre)\b", "in a dim cinema", "sitting"),
    (r"\b(pool|swimming pool)\b", "by a swimming pool", ""),
    (r"\b(car|cab|taxi|uber)\b", "in the back of a car", "sitting"),
    (r"\b(train|metro|subway)\b", "on a train by the window", "sitting"),
    (r"\b(bus)\b", "on a bus by the window", "sitting"),
    (r"\b(street|road|outside|sidewalk|walking)\b", "on a city street", "standing"),
    (r"\b(desk|office)\b", "at a desk", "sitting"),
    (r"\b(sofa|couch)\b", "on a couch in a cozy living room", "sitting"),
    (r"\b(bed|bedroom|covers|blanket|duvet)\b", "in her cozy bedroom", "on her bed"),
    (r"\b(my room|room)\b", "in her cozy room with a warm lamp glow", ""),
    (r"\b(home|house|flat|apartment|hostel)\b", "at home in a cozy room", ""),
]
_PLACES_RE = [(re.compile(p, re.I), place, pose) for p, place, pose in _PLACES]

# ---------------------------------------------------------------- poses / activities
_POSES: List[Tuple[str, str]] = [
    (r"\b(lying|laying|lay|sprawled|flopped|in bed)\b", "lying down"),
    (r"\b(curled up|curled)\b", "curled up"),
    (r"\b(sitting|seated|chilling|lounging|perched)\b", "sitting relaxed"),
    (r"\b(standing|leaning)\b", "standing"),
    (r"\b(walking|strolling)\b", "walking"),
]
_POSES_RE = [(re.compile(p, re.I), v) for p, v in _POSES]

_DRINKS = r"(coffee|latte|cappuccino|espresso|tea|chai|boba|smoothie|juice|milkshake|hot chocolate|cold coffee)"
_ACTIVITIES: List[Tuple[str, str]] = [
    (rf"\b(?:sipping|drinking|having|with (?:a|my)?)\s*(?:a |my |some |an |iced |hot |cold )?{_DRINKS}\b", ""),   # handled specially
    (r"\b(reading|book|novel)\b", "reading a book"),
    (r"\b(studying|homework|assignment|revising|notes)\b", "studying with notebooks"),
    (r"\b(watching)\b.{0,25}\b(tv|movie|film|netflix|show|series|anime|drama)\b", "watching a movie"),
    (r"\b(headphones|earphones|listening to music|listening to)\b", "wearing headphones, listening to music"),
    (r"\b(scrolling|on my phone|texting|my phone)\b", "looking at her phone"),
    (r"\b(cooking|baking)\b", "cooking"),
    (r"\b(eating|snacking|snack|lunch|dinner|breakfast|pizza|ice cream|noodles|maggi)\b", "eating a snack"),
    (r"\b(dancing)\b", "dancing"),
    (r"\b(drawing|sketching|painting)\b", "sketching in a notebook"),
    (r"\b(yoga|stretching|working out|workout)\b", "stretching"),
    (r"\b(doing my makeup|doing my hair|my makeup|my hair)\b", "fixing her hair"),
    (r"\b(napping|sleepy|half asleep|can't sleep|cant sleep)\b", "sleepy, eyes half closed"),
    (r"\b(shopping)\b", "shopping"),
]
_ACTIVITIES_RE = [(re.compile(p, re.I), v) for p, v in _ACTIVITIES]
_DRINK_RE = re.compile(_ACTIVITIES[0][0], re.I)

# ---------------------------------------------------------------- outfit / mood (kept SFW)
_OUTFITS: List[Tuple[str, str]] = [
    (r"\b(pajamas|pyjamas|pjs|pj's|nightwear)\b", "cozy pajamas"),
    (r"\b(hoodie)\b", "an oversized hoodie"),
    (r"\b(sweater|sweatshirt|jumper)\b", "a cozy oversized sweater"),
    (r"\b(oversized (?:t-?shirt|tee|shirt))\b", "an oversized t-shirt"),
    (r"\b(t-?shirt|tee)\b", "a t-shirt"),
    (r"\b(dress|gown)\b", "a dress"),
    (r"\b(jeans|denim)\b", "jeans and a casual top"),
    (r"\b(saree|sari)\b", "a saree"),
    (r"\b(kurta|salwar|lehenga)\b", "a kurta"),
    (r"\b(jacket|coat)\b", "a jacket"),
    (r"\b(uniform)\b", "a school-style uniform"),
    (r"\b(sweatpants|joggers|trackpants|track pants)\b", "sweatpants and a loose top"),
]
_OUTFITS_RE = [(re.compile(p, re.I), v) for p, v in _OUTFITS]

_MOODS: List[Tuple[str, str]] = [
    (r"\b(bored|boring)\b", "bored"),
    (r"\b(tired|sleepy|exhausted|drained)\b", "tired"),
    (r"\b(happy|excited|good mood|great mood|giggling)\b", "happy, smiling softly"),
    (r"\b(annoyed|irritated|angry|mad|pissed)\b", "annoyed"),
    (r"\b(sad|lonely|down|blue|moody)\b", "wistful"),
    (r"\b(nervous|anxious|stressed)\b", "nervous"),
    (r"\b(chill|relaxed|cozy|comfy|peaceful)\b", "relaxed"),
]
_MOODS_RE = [(re.compile(p, re.I), v) for p, v in _MOODS]

# ---------------------------------------------------------------- sentence filters
_SPLIT = re.compile(r"(?<=[.!?…])\s+|\n+")
_SELF = re.compile(r"\b(i'?m|i’m|im|i am|i just|i'?m just|currently|rn|right now)\b", re.I)
_FRAGMENT = re.compile(
    r"^\s*(?:ugh,?\s*|just\s*|currently\s*|still\s*|hm+,?\s*|well,?\s*)?"
    r"(?:lying|laying|sitting|sprawled|curled|chilling|lounging|standing|walking|sipping|drinking|"
    r"reading|studying|watching|eating|cooking|listening|scrolling|stuck|waiting|at|in|on)\b", re.I)
_REJECT = re.compile(
    r"\?|\b(not|n't|never|nowhere|wasn't|weren't|was|were|went|used to|would|wish|if i|when i|"
    r"gonna|going to|will|tomorrow|tonight|later|yesterday|someday|planning|want to|wanna)\b", re.I)
# "going to" is future, but "i'm at the park" must survive "i'm" (which contains no reject word)


def _clean_sentences(text: str) -> List[str]:
    """Statements only: no questions, negations, past or future."""
    out = []
    for raw in _SPLIT.split(text or ""):
        s = raw.strip().strip("*_~").lower()
        s = re.sub(r"\[send_selfie:[^\]]*\]", "", s).strip()
        if s and not _REJECT.search(s):
            out.append(s)
    return out


def _present_self_sentences(text: str) -> List[str]:
    return [s for s in _clean_sentences(text) if _SELF.search(s) or _FRAGMENT.match(s)]


def _first(rules, text):
    for rx, val in rules:
        m = rx.search(text)
        if m:
            return m, val
    return None, None


def extract_scene(reply: str) -> Optional[Dict[str, str]]:
    """Fields (place, activity, outfit, pose, mood) she stated about herself right now,
    or None if she didn't say where she is or what she's doing."""
    sentences = _present_self_sentences(reply)
    if not sentences:
        return None
    text = " ".join(sentences)

    scene: Dict[str, str] = {}

    place_default_pose = ""
    for rx, place, pose in _PLACES_RE:
        if rx.search(text):
            scene["place"] = place
            place_default_pose = pose
            break

    # pose: an explicit verb wins over the place's default
    _m, pose_word = _first(_POSES_RE, text)
    on_bed = bool(re.search(r"\b(bed|covers|blanket|duvet)\b", text))
    if pose_word:
        if on_bed and pose_word in ("lying down", "curled up", "sitting relaxed"):
            scene["pose"] = {"lying down": "lying on her bed", "curled up": "curled up on her bed",
                             "sitting relaxed": "sitting on her bed"}[pose_word]
        else:
            scene["pose"] = pose_word
    elif place_default_pose:
        scene["pose"] = {"on her bed": "lying on her bed", "sitting": "sitting relaxed",
                         "standing": "standing"}.get(place_default_pose, place_default_pose)

    # activity
    dm = _DRINK_RE.search(text)
    if dm:
        scene["activity"] = f"holding a cup of {dm.group(1)}"
    else:
        _m, act = _first(_ACTIVITIES_RE[1:], text)
        if act:
            scene["activity"] = act

    # outfit and mood may sit in their own short sentence ("bored."), so look at all statements
    whole = " ".join(_clean_sentences(reply))
    _m, outfit = _first(_OUTFITS_RE, whole)
    if outfit:
        scene["outfit"] = outfit
    _m, mood = _first(_MOODS_RE, whole)
    if mood:
        scene["mood"] = mood

    # nothing about where she is or what she's doing -> no scene (mood/outfit alone isn't a scene)
    if not any(k in scene for k in ("place", "pose", "activity")):
        return None
    return scene
