# web/browser.py — Fetch a URL and return clean text.

import re
import requests
from html.parser import HTMLParser
from typing import Dict


USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"
)

TIMEOUT = 15
MAX_TEXT = 20000


class _TextExtractor(HTMLParser):
    """Pull visible text out of HTML. Skips script/style/noscript/iframe."""

    SKIP = {"script", "style", "noscript", "iframe", "svg", "head"}
    BLOCK = {
        "p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6",
        "section", "article", "header", "footer", "blockquote",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self._skip_depth = 0
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self.SKIP:
            self._skip_depth += 1
        elif tag == "title":
            self._in_title = True
        elif tag in self.BLOCK and self._skip_depth == 0:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.SKIP and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tag == "title":
            self._in_title = False
        elif tag in self.BLOCK and self._skip_depth == 0:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._skip_depth == 0 and data:
            self.parts.append(data)

    def text(self) -> str:
        raw = "".join(self.parts)
        raw = re.sub(r"[ \t\r\f\v]+", " ", raw)
        raw = re.sub(r"\n\s*\n+", "\n\n", raw)
        return raw.strip()


class Browser:
    """Minimal HTTP fetcher. Returns dict: ok, url, title, text, error."""

    def __init__(self, user_agent: str = USER_AGENT, timeout: int = TIMEOUT):
        self.headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.timeout = timeout

    def fetch(self, url: str) -> Dict:
        if not url or not url.startswith(("http://", "https://")):
            return {"ok": False, "url": url, "title": "", "text": "",
                    "error": "invalid url"}

        try:
            r = requests.get(url, headers=self.headers, timeout=self.timeout,
                             allow_redirects=True)
        except requests.exceptions.Timeout:
            return {"ok": False, "url": url, "title": "", "text": "",
                    "error": "timeout"}
        except requests.exceptions.RequestException as e:
            return {"ok": False, "url": url, "title": "", "text": "",
                    "error": f"request failed: {type(e).__name__}"}

        if r.status_code != 200:
            return {"ok": False, "url": url, "title": "", "text": "",
                    "error": f"http {r.status_code}"}

        ctype = r.headers.get("Content-Type", "").lower()
        if "html" not in ctype and "xml" not in ctype:
            if "text/" in ctype:
                return {"ok": True, "url": r.url, "title": "",
                        "text": r.text[:MAX_TEXT], "error": None}
            return {"ok": False, "url": url, "title": "", "text": "",
                    "error": f"unsupported content-type: {ctype}"}

        parser = _TextExtractor()
        try:
            parser.feed(r.text)
        except Exception as e:
            return {"ok": False, "url": url, "title": "", "text": "",
                    "error": f"parse error: {e}"}

        text = parser.text()
        if len(text) > MAX_TEXT:
            text = text[:MAX_TEXT]

        return {
            "ok": True,
            "url": r.url,
            "title": (parser.title or "").strip()[:200],
            "text": text,
            "error": None,
        }


if __name__ == "__main__":
    b = Browser()
    r = b.fetch("https://en.wikipedia.org/wiki/Artificial_intelligence")
    print("ok:", r["ok"], "| title:", r["title"])
    print("error:", r["error"])
    print("text length:", len(r["text"]))
    print(r["text"][:300])
