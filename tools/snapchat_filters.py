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

    return img

FILTERS = ["none", "dog", "cat", "bunny", "glasses", "mustache", "crown", "hearts",
           "beauty", "vintage", "neon", "glitch", "grayscale", "cool", "warm",
           "cyberpunk", "thermal"]
