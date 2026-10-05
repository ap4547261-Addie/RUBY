# tools/vision.py
import os
import cv2
from PIL import Image

_captioner = None

def _load_captioner():
    """Lazy-load BLIP captioner. Downloads ~1GB on first run."""
    global _captioner
    if _captioner is not None:
        return _captioner
    try:
        from transformers import BlipProcessor, BlipForConditionalGeneration
        print("👁️ Loading BLIP vision model (first run may take 1-2 min)...")
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        _captioner = (processor, model)
        print("✅ Vision model loaded.")
    except Exception as e:
        print(f"⚠️ Vision model failed to load: {e}")
        _captioner = False
    return _captioner


def caption_image(image_path: str) -> str:
    """Returns a short text description of a single image."""
    loaded = _load_captioner()
    if not loaded:
        return "[vision unavailable]"
    processor, model = loaded
    try:
        image = Image.open(image_path).convert("RGB")
        inputs = processor(image, return_tensors="pt")
        out = model.generate(**inputs, max_new_tokens=40)
        caption = processor.decode(out[0], skip_special_tokens=True)
        return caption.strip()
    except Exception as e:
        return f"[vision error: {e}]"


def caption_video(video_path: str, max_frames: int = 8) -> str:
    """Extracts up to N evenly-spaced frames from a video and captions each."""
    loaded = _load_captioner()
    if not loaded:
        return "[vision unavailable]"
    processor, model = loaded
    try:
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        duration = total_frames / fps if fps > 0 else 0

        if total_frames <= 0:
            cap.release()
            return "[video unreadable]"

        # Sample frames evenly across the clip
        step = max(1, total_frames // max_frames)
        captions = []
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % step == 0:
                pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                inputs = processor(pil, return_tensors="pt")
                out = model.generate(**inputs, max_new_tokens=40)
                cap_text = processor.decode(out[0], skip_special_tokens=True).strip()
                seconds = round(frame_idx / fps, 1)
                captions.append(f"[{seconds}s] {cap_text}")
                if len(captions) >= max_frames:
                    break
            frame_idx += 1
        cap.release()

        if not captions:
            return "[no frames extracted]"

        header = f"Video ({round(duration, 1)}s long, {len(captions)} frames sampled):"
        return header + "\n" + "\n".join(captions)
    except Exception as e:
        return f"[video vision error: {e}]"
