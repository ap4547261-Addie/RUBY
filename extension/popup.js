function refresh() {
  chrome.runtime.sendMessage({ action: "status" }, (s) => {
    const el = document.getElementById("status");
    if (!s) { el.textContent = "Ruby not running"; return; }
    el.textContent = s.connected ? "✅ Connected to Ruby" : `⏳ Waiting (queue ${s.queued})`;
  });
}
document.getElementById("send").onclick = () => {
  chrome.runtime.sendMessage({ action: "scrapeNow" });
};
refresh();
setInterval(refresh, 2000);
