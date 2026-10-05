# tools/ruby_selfie.py
import os
import glob
from PIL import Image
from tools.snapchat_filters import apply_filter, FILTERS

class RubySelfieGenerator:
    """Generates filtered selfies of Ruby using her original photo, keeping her face identical."""

    CANDIDATE_NAMES = [
        "ruby_base.jpg", "ruby_base.png", "ruby_base.jpeg",
        "ruby.jpg", "ruby.png",
        "RUBY_03.png", "RUBY_03.jpg",
        "reference.jpg", "reference.png",
        "ruby_reference.jpg", "ruby_reference.png",
    ]

    CANDIDATE_DIRS = [".", "RUBY", "assets", "images", "reference"]

    def __init__(self, output_dir="ruby_selfies"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.base_image_path = self._find_reference()
        if self.base_image_path:
            print(f"✅ RubySelfieGenerator found reference: {self.base_image_path}")
        else:
            print("⚠️ RubySelfieGenerator: no reference image found. Put a photo at 'ruby_base.jpg'.")

    def _find_reference(self):
        for folder in self.CANDIDATE_DIRS:
            if not os.path.isdir(folder):
                continue
            for name in self.CANDIDATE_NAMES:
                path = os.path.join(folder, name)
                if os.path.exists(path):
                    return path
        for ext in ("png", "jpg", "jpeg"):
            matches = glob.glob(f"RUBY/RUBY*.{ext}")
            if matches:
                return matches[0]
        return None

    def generate(self, prompt: str) -> dict:
        if not self.base_image_path:
            return {"ok": False, "error": "No reference photo found. Save one at 'ruby_base.jpg'."}

        lower = prompt.lower()
        chosen_filter = "none"
        filter_keywords = {
            "cyberpunk": ["cyberpunk", "hacker", "futuristic"],
            "vintage":   ["vintage", "retro", "old", "sepia", "nostalgic"],
            "glitch":    ["glitch", "hacked", "error", "digital"],
            "thermal":   ["thermal", "heat", "infrared"],
            "grayscale": ["black and white", "monochrome", "grayscale", "noir"],
            "warm":      ["warm", "sunset", "cozy"],
            "cool":      ["cold", "blue", "chill", "winter", "sad"],
            "beauty":    ["pretty", "beautiful", "soft", "smooth"],
            "neon":      ["party", "vibe", "club", "neon", "excited"],
            "glasses":   ["sunglasses", "shades", "glasses"],
            "crown":     ["crown", "queen", "princess"],
            "hearts":    ["love", "hearts", "valentine"],
        }
        for filter_name, keywords in filter_keywords.items():
            if any(kw in lower for kw in keywords):
                chosen_filter = filter_name
                break

        try:
            base = Image.open(self.base_image_path).convert("RGB")
            result_img = apply_filter(base, chosen_filter)
            safe_filter = chosen_filter.replace(" ", "_")
            out_path = os.path.join(self.output_dir, f"ruby_{safe_filter}.jpg")
            result_img.save(out_path, quality=90)
            print(f"📸 Ruby selfie generated: {out_path} (filter: {chosen_filter})")
            return {"ok": True, "path": out_path, "filter": chosen_filter}
        except Exception as e:
            return {"ok": False, "error": str(e)}
