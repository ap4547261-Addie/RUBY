// content.js — scrape page and forward to background
(function () {
  if (window.__rubyLoaded) return;
  window.__rubyLoaded = true;

  function platform() {
    const h = location.hostname;
    if (h.includes("instagram.com")) return "instagram";
    if (h.includes("youtube.com")) return "youtube";
    if (h.includes("reddit.com")) return "reddit";
    if (h.includes("twitter.com") || h.includes("x.com")) return "twitter";
    if (h.includes("facebook.com")) return "facebook";
    if (h.includes("linkedin.com")) return "linkedin";
    if (h.includes("tiktok.com")) return "tiktok";
    if (h.includes("pinterest.com")) return "pinterest";
    return "web";
  }

  function scrape() {
    const title = document.title || "";
    const body = (document.body ? document.body.innerText : "").slice(0, 12000);
    return { title, body, url: location.href, platform: platform() };
  }

  function send() {
    const p = scrape();
    const content = `Title: ${p.title}\nURL: ${p.url}\n\n${p.body}`;
    chrome.runtime.sendMessage({
      action: "streamContent",
      platform: p.platform,
      content,
      url: p.url,
    }, (resp) => console.log("[Ruby]", resp));
  }

  chrome.runtime.onMessage.addListener((msg, s, sendResponse) => {
    if (msg.action === "doScrape") { send(); sendResponse({ ok: true }); }
    return true;
  });

  window.addEventListener("load", () => setTimeout(send, 2500));
})();
