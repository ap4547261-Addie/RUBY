# web/web_learning.py — Extract topics, keywords, summary from page text.

import re
from typing import Dict, List


STOPWORDS = {
    "the", "and", "for", "are", "but", "not", "you", "all", "any", "can",
    "had", "her", "was", "one", "our", "out", "day", "get", "has", "him",
    "his", "how", "man", "new", "now", "old", "see", "two", "way", "who",
    "boy", "did", "its", "let", "put", "say", "she", "too", "use", "that",
    "with", "have", "this", "will", "your", "from", "they", "know", "want",
    "been", "good", "much", "some", "time", "very", "when", "come", "here",
    "just", "like", "long", "make", "many", "more", "only", "over", "such",
    "take", "than", "them", "well", "were", "what", "also", "into", "than",
    "then", "these", "about", "would", "there", "their", "which", "could",
    "other", "after", "first", "never", "these", "being", "under", "where",
    "while", "should", "before", "because", "through", "between",
}


class WebLearning:
    """Turn raw page text into structured learning material."""

    def __init__(self, min_word_len: int = 4, max_keywords: int = 20):
        self.min_word_len = min_word_len
        self.max_keywords = max_keywords

    def keywords(self, text: str) -> List[str]:
        words = re.findall(r"[a-zA-Z']+", text.lower())
        counts = {}
        for w in words:
            if len(w) < self.min_word_len:
                continue
            if w in STOPWORDS:
                continue
            counts[w] = counts.get(w, 0) + 1
        ranked = sorted(counts.items(), key=lambda x: -x[1])
        return [w for w, _ in ranked[:self.max_keywords]]

    def summary(self, text: str, max_sentences: int = 3) -> str:
        # split on sentence boundaries
        parts = re.split(r"(?<=[.!?])\s+", text.strip())
        parts = [p.strip() for p in parts if len(p.strip()) > 20]
        if not parts:
            return text[:300]
        return " ".join(parts[:max_sentences])[:500]

    def importance(self, text: str, keywords: List[str]) -> int:
        """Rough importance score 1-5."""
        length_score = min(len(text) // 4000, 3)  # 0..3
        keyword_score = min(len(keywords) // 5, 1)  # 0..1
        score = 2 + length_score + keyword_score
        return max(1, min(5, score))

    def process(self, title: str, text: str, url: str) -> Dict:
        """Full processing: returns dict ready for ingestion."""
        kws = self.keywords(text)
        summ = self.summary(text)
        imp = self.importance(text, kws)

        # Build a compact learning block
        learning_block = (
            f"Source: {url}\n"
            f"Title: {title}\n"
            f"Summary: {summ}\n"
            f"Keywords: {', '.join(kws)}\n"
            f"Body: {text[:8000]}"
        )

        return {
            "url": url,
            "title": title,
            "summary": summ,
            "keywords": kws,
            "importance": imp,
            "text": learning_block,
            "raw_length": len(text),
        }


if __name__ == "__main__":
    wl = WebLearning()
    sample = (
        "Artificial intelligence is intelligence exhibited by machines. "
        "It is a field of research in computer science that develops and "
        "studies methods and software that enable machines to perceive "
        "their environment and use learning and intelligence to take "
        "actions that maximize their chances of achieving defined goals."
    )
    out = wl.process("AI", sample, "https://example.com/ai")
    print("importance:", out["importance"])
    print("keywords:", out["keywords"][:10])
    print("summary:", out["summary"])
