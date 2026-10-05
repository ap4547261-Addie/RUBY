# tools/snapchat_filters.py
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps

_face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def detect_faces(pil_img):
    frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return _face_cascade.detectMultiScale(gray, 1.1, 4)

def apply_filter(pil_img, filter_name):
    img = pil_img.convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")
    faces = detect_faces(img)

    # ========================================================
    # FACE-ATTACHED FILTERS (dog, cat, bunny, glasses, etc.)
    # ========================================================
    for (x, y, w, h) in faces:
        if filter_name == "dog":
            ew, eh = w // 3, h // 3
            draw.ellipse([x - ew//4, y - eh, x + ew, y], fill=(80, 40, 20, 230))
            draw.ellipse([x + w - ew, y - eh, x + w + ew//4, y], fill=(80, 40, 20, 230))
            nx, ny = x + w//2, y + h*2//3
            draw.ellipse([nx - w//10, ny - h//12, nx + w//10, ny + h//12], fill=(30, 20, 20, 240))
            draw.ellipse([nx - w//3, ny + h//8, nx + w//3, ny + h//3], fill=(220, 80, 80, 180))
        elif filter_name == "cat":
            eh = h // 3
            draw.polygon([(x, y), (x + w//4, y - eh), (x + w//2, y)], fill=(20, 20, 20, 240))
            draw.polygon([(x + w//2, y), (x + 3*w//4, y - eh), (x + w, y)], fill=(20, 20, 20, 240))
            cx, cy = x + w//2, y + h*2//3
            for i in range(-1, 2):
                draw.line([(cx - w//3, cy + i*10), (cx - w//8, cy)], fill=(255,255,255,200), width=2)
                draw.line([(cx + w//3, cy + i*10), (cx + w//8, cy)], fill=(255,255,255,200), width=2)
        elif filter_name == "bunny":
            ew, eh = w // 5, int(h * 1.2)
            draw.ellipse([x + w//4 - ew, y - eh, x + w//4 + ew, y], fill=(255, 220, 230, 220))
            draw.ellipse([x + 3*w//4 - ew, y - eh, x + 3*w//4 + ew, y], fill=(255, 220, 230, 220))
            draw.ellipse([x + w//4 - ew//2, y - eh + 20, x + w//4 + ew//2, y - 10], fill=(255, 150, 180, 200))
            draw.ellipse([x + 3*w//4 - ew//2, y - eh + 20, x + 3*w//4 + ew//2, y - 10], fill=(255, 150, 180, 200))
        elif filter_name == "glasses":
            gx1, gx2, gy, gh = x + w//8, x + w - w//8, y + h//3, h//6
            draw.rounded_rectangle([gx1, gy, x + w//2 - 5, gy + gh], radius=8, fill=(20, 20, 20, 235))
            draw.rounded_rectangle([x + w//2 + 5, gy, gx2, gy + gh], radius=8, fill=(20, 20, 20, 235))
            draw.line([(x + w//2 - 5, gy + gh//2), (x + w//2 + 5, gy + gh//2)], fill=(20,20,20,235), width=4)
        elif filter_name == "mustache":
            my = y + h*2//3
            draw.ellipse([x + w//4, my, x + w//2, my + h//8], fill=(30, 20, 15, 240))
            draw.ellipse([x + w//2, my, x + 3*w//4, my + h//8], fill=(30, 20, 15, 240))
        elif filter_name == "crown":
            cy = y - h//8
            draw.polygon([
                (x + w//4, cy), (x + w//4 + w//12, cy - h//5), (x + w//2 - w//8, cy),
                (x + w//2, cy - h//4), (x + w//2 + w//8, cy),
                (x + 3*w//4 - w//12, cy - h//5), (x + 3*w//4, cy),
                (x + 3*w//4, cy + h//8), (x + w//4, cy + h//8),
            ], fill=(255, 200, 0, 240), outline=(180, 130, 0, 255))
        elif filter_name == "hearts":
            for i in range(3):
                hx = x - w//2 + i * (w//2)
                hy = y - h//4 + (i % 2) * h//6
                draw.ellipse([hx, hy, hx + w//4, hy + h//5], fill=(255, 80, 130, 200))
                draw.ellipse([hx + w//8, hy, hx + 3*w//8, hy + h//5], fill=(255, 80, 130, 200))
                draw.polygon([(hx, hy + h//8), (hx + w//4, hy + h//8), (hx + w//8, hy + h//4)], fill=(255, 80, 130, 200))

    # ========================================================
    # FULL-FRAME FILTERS
    # ========================================================
    if filter_name == "beauty":
        img = img.filter(ImageFilter.GaussianBlur(1.2))
        img = ImageEnhance.Brightness(img).enhance(1.08)
        img = ImageEnhance.Color(img).enhance(1.1)
    elif filter_name == "vintage":
        img = ImageOps.colorize(ImageOps.grayscale(img), "#2b1810", "#f0d0a0")
    elif filter_name == "neon":
        overlay = Image.new("RGB", img.size, (255, 0, 128))
        img = Image.blend(img, overlay, 0.2)
        img = ImageEnhance.Contrast(img).enhance(1.4)
    elif filter_name == "glitch":
        r, g, b = img.split()
        r = r.transform(r.size, Image.AFFINE, (1, 0, -6, 0, 1, 0))
        b = b.transform(b.size, Image.AFFINE, (1, 0, 6, 0, 1, 0))
        img = Image.merge("RGB", (r, g, b))
    elif filter_name == "grayscale":
        img = ImageOps.grayscale(img).convert("RGB")
    elif filter_name == "cool":
        overlay = Image.new("RGB", img.size, (0, 100, 200))
        img = Image.blend(img, overlay, 0.15)
    elif filter_name == "warm":
        overlay = Image.new("RGB", img.size, (255, 140, 0))
        img = Image.blend(img, overlay, 0.15)
    elif filter_name == "cyberpunk":
        overlay = Image.new("RGB", img.size, (150, 0, 200))
        img = Image.blend(img, overlay, 0.25)
        img = ImageEnhance.Contrast(img).enhance(1.5)
    elif filter_name == "thermal":
        img = ImageOps.colorize(ImageOps.grayscale(img), "#000080", "#ff0000")

    # ========================================================
    # NEW FILTERS (Option B additions)
    # ========================================================
    elif filter_name == "Nostalgia":
        # Faded old-photo look with soft warm tint and slight grain
        img = ImageOps.colorize(ImageOps.grayscale(img), "#3d2a1a", "#e8d5b0")
        img = ImageEnhance.Color(img).enhance(0.6)
        img = ImageEnhance.Brightness(img).enhance(0.95)
        # Add subtle grain
        np_img = np.array(img).astype(np.int16)
        noise = np.random.randint(-12, 12, np_img.shape, dtype=np.int16)
        np_img = np.clip(np_img + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(np_img)
        img = img.filter(ImageFilter.GaussianBlur(0.6))

    elif filter_name == "CINEMATIC BARS":
        # Widescreen letterbox with a subtle teal-orange grade
        img = ImageEnhance.Contrast(img).enhance(1.2)
        img = ImageEnhance.Color(img).enhance(1.15)
        # Teal shadows + orange highlights (Hollywood grade)
        np_img = np.array(img).astype(np.float32)
        np_img[:, :, 0] = np.clip(np_img[:, :, 0] * 1.08, 0, 255)   # R up
        np_img[:, :, 2] = np.clip(np_img[:, :, 2] * 1.05, 0, 255)   # B up
        np_img[:, :, 1] = np.clip(np_img[:, :, 1] * 0.96, 0, 255)   # G down
        img = Image.fromarray(np_img.astype(np.uint8))
        # Add black bars top and bottom (cinema letterbox)
        W, H = img.size
        bar_height = int(H * 0.12)
        overlay = Image.new("RGB", (W, H), (0, 0, 0))
        img.paste(overlay, (0, 0))
        img.paste(overlay, (0, H - bar_height))

    elif filter_name == "Shadow":
        # High contrast dark moody look — deep shadows, cool tones
        img = ImageEnhance.Contrast(img).enhance(1.6)
        img = ImageEnhance.Brightness(img).enhance(0.75)
        overlay = Image.new("RGB", img.size, (10, 5, 30))
        img = Image.blend(img, overlay, 0.25)
        img = ImageEnhance.Color(img).enhance(0.7)

    elif filter_name == "Disposable Hard":
        # Harsh flash-photo look — blown highlights, crushed blacks, greenish tint
        img = ImageEnhance.Contrast(img).enhance(1.8)
        img = ImageEnhance.Brightness(img).enhance(1.15)
        # Green-cyan tint typical of cheap disposable camera flashes
        np_img = np.array(img).astype(np.float32)
        np_img[:, :, 0] = np.clip(np_img[:, :, 0] * 0.92, 0, 255)  # R down
        np_img[:, :, 1] = np.clip(np_img[:, :, 1] * 1.05, 0, 255)  # G up
        np_img[:, :, 2] = np.clip(np_img[:, :, 2] * 1.02, 0, 255)  # B up
        img = Image.fromarray(np_img.astype(np.uint8))
        # Vignette (dark edges like a cheap lens)
        W, H = img.size
        vignette = Image.new("L", (W, H), 0)
        vdraw = ImageDraw.Draw(vignette)
        vdraw.ellipse([-W*0.2, -H*0.2, W*1.2, H*1.2], fill=255)
        vignette = vignette.filter(ImageFilter.GaussianBlur(W//8))
        black = Image.new("RGB", (W, H), (0, 0, 0))
        img = Image.composite(img, black, vignette)
        # Slight grain
        np_img = np.array(img).astype(np.int16)
        noise = np.random.randint(-18, 18, np_img.shape, dtype=np.int16)
        np_img = np.clip(np_img + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(np_img)

    return img

FILTERS = [
    "none",
    # Face-attached
    "dog", "cat", "bunny", "glasses", "mustache", "crown", "hearts",
    # Color / mood
    "beauty", "vintage", "neon", "glitch", "grayscale", "cool", "warm",
    "cyberpunk", "thermal",
    # Cinematic / stylized (new)
    "Nostalgia", "CINEMATIC BARS", "Shadow", "Disposable Hard",
]
