{
  "manifest_version": 3,
  "name": "Ruby Bridge",
  "version": "1.0",
  "description": "Streams page content to Ruby",
  "permissions": ["activeTab", "scripting", "tabs"],
  "host_permissions": ["<all_urls>"],
  "background": { "service_worker": "background.js" },
  "action": { "default_popup": "popup.html", "default_title": "Ruby" },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ]
}
