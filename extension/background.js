// background.js — WebSocket client to Ruby
const RUBY_URL = "ws://127.0.0.1:8765";
let ws = null;
let queue = [];
let lastSent = 0;

function connect() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;
  try {
    ws = new WebSocket(RUBY_URL);
    ws.onopen = () => {
      console.log("[Ruby] connected");
      while (queue.length) ws.send(JSON.stringify(queue.shift()));
    };
    ws.onmessage = (e) => {
      try { console.log("[Ruby ack]", JSON.parse(e.data)); } catch(_) {}
    };
    ws.onclose = () => setTimeout(connect, 3000);
    ws.onerror = () => {};
  } catch (e) { setTimeout(connect, 3000); }
}

function sendToRuby(payload) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(payload));
    return true;
  }
  queue.push(payload);
  connect();
  return false;
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "streamContent") {
    const now = Date.now();
    if (now - lastSent < 15000) { sendResponse({ ok: false, reason: "throttled" }); return true; }
    lastSent = now;
    const ok = sendToRuby({
      type: "content",
      platform: msg.platform || "web",
      content: msg.content || "",
      url: msg.url || "",
      timestamp: new Date().toISOString(),
    });
    sendResponse({ ok, queued: queue.length });
  } else if (msg.action === "status") {
    sendResponse({ connected: !!ws && ws.readyState === WebSocket.OPEN, queued: queue.length });
  } else if (msg.action === "scrapeNow") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) chrome.tabs.sendMessage(tabs[0].id, { action: "doScrape" });
    });
    sendResponse({ ok: true });
  }
  return true;
});

connect();
setInterval(() => { if (!ws || ws.readyState > 1) connect(); }, 5000);
