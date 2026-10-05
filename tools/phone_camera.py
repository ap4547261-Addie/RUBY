# tools/phone_camera.py
import cv2
import io
import base64
import time
import os
import numpy as np
from datetime import datetime
from PIL import Image
import flet as ft

from tools.snapchat_filters import apply_filter, FILTERS


class PhoneCamera:
    """Phone-style camera with photo + video recording, low-quality mode for smooth performance."""

    def __init__(self, page: ft.Page, snaps_dir="snaps"):
        self.page = page
        self.snaps_dir = snaps_dir
        os.makedirs(self.snaps_dir, exist_ok=True)

    def open(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self._snack("❌ No webcam found")
            return

        # Low-quality for smooth performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        cap.set(cv2.CAP_PROP_FPS, 15)

        current_filter = {"name": "none"}
        running = {"on": True}
        recording = {"active": False, "writer": None, "path": None, "start": 0}

        cam_img = ft.Image(width=400, height=520, fit=ft.ImageFit.COVER,
                           border_radius=20, gapless_playback=True)
        filter_label = ft.Text("none", size=13, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
        rec_timer = ft.Text("00:00", size=14, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
        rec_indicator = ft.Container(
            content=ft.Row([
                ft.Container(width=10, height=10, bgcolor=ft.Colors.RED_400, border_radius=5),
                rec_timer,
            ], spacing=5),
            bgcolor="#00000088", border_radius=10,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            top=10, right=10, visible=False,
        )

        def set_filter(name):
            current_filter["name"] = name
            filter_label.value = name
            self.page.update()

        filter_chips = ft.Row(
            [ft.Container(
                content=ft.Text(f, size=11, color=ft.Colors.WHITE),
                bgcolor="#2A2A36", border_radius=15,
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                on_click=lambda ev, f=f: set_filter(f),
            ) for f in FILTERS],
            scroll=ft.ScrollMode.AUTO, spacing=6,
        )

        def snap(ev):
            ret, frame = cap.read()
            if not ret:
                return
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil = apply_filter(Image.fromarray(frame), current_filter["name"])
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fpath = os.path.join(self.snaps_dir, f"snap_{ts}_{current_filter['name']}.jpg")
            pil.save(fpath, quality=60)
            print(f"📸 Snap saved: {fpath}")
            self._snack(f"📸 Photo saved!")

        def toggle_recording(ev):
            if not recording["active"]:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                fpath = os.path.join(self.snaps_dir, f"video_{ts}_{current_filter['name']}.mp4")
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                out = cv2.VideoWriter(fpath, fourcc, 15.0, (w, h))
                recording.update({"active": True, "writer": out, "path": fpath, "start": time.time()})
                rec_indicator.visible = True
                rec_timer.value = "00:00"
                print(f"🎥 Recording started: {fpath}")
            else:
                recording["active"] = False
                if recording["writer"]:
                    recording["writer"].release()
                recording["writer"] = None
                rec_indicator.visible = False
                print(f"🎥 Recording stopped: {recording['path']}")
                self._snack("🎥 Video saved!")

        def open_gallery(ev):
            files = sorted(
                [f for f in os.listdir(self.snaps_dir) if f.endswith((".jpg", ".mp4"))],
                reverse=True,
            )[:30]
            if not files:
                self._snack("📭 No snaps yet!")
                return

            items = []
            for f in files:
                is_vid = f.endswith(".mp4")
                items.append(ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PLAY_CIRCLE_FILLED if is_vid else ft.Icons.IMAGE,
                                size=40, color=ft.Colors.PINK_400),
                        ft.Text(f[:12] + "...", size=10, color=ft.Colors.WHITE),
                    ], alignment=ft.MainAxisAlignment.CENTER,
                       horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    width=140, height=140, bgcolor="#2A2A36",
                    border_radius=12, alignment=ft.alignment.center,
                    on_click=lambda ev, fp=os.path.join(self.snaps_dir, f): preview_snap(fp),
                ))

            g_dialog = ft.AlertDialog(
                title=ft.Text(f"🖼️ Gallery ({len(files)} items)"),
                content=ft.Container(
                    content=ft.GridView(items, runs_count=4, max_extent=160,
                                        spacing=8, run_spacing=8, expand=True),
                    width=680, height=520,
                ),
                actions=[ft.TextButton("Close", on_click=lambda ev: self.page.close(g_dialog))],
            )
            self.page.open(g_dialog)

        def preview_snap(path):
            is_vid = path.endswith(".mp4")
            p_dialog = ft.AlertDialog(
                title=ft.Text(os.path.basename(path)),
                content=ft.Container(
                    content=ft.Text("🎥 Video saved. Open in player.", color=ft.Colors.WHITE)
                    if is_vid else ft.Image(src=path, width=500, fit=ft.ImageFit.CONTAIN),
                    padding=20,
                ),
                actions=[
                    ft.TextButton("Delete", on_click=lambda ev: (os.remove(path), self.page.close(p_dialog))),
                    ft.TextButton("Close", on_click=lambda ev: self.page.close(p_dialog)),
                ],
            )
            self.page.open(p_dialog)

        def close_camera(ev):
            if recording["active"]:
                recording["active"] = False
                if recording["writer"]:
                    recording["writer"].release()
            running["on"] = False
            time.sleep(0.15)
            try:
                cap.release()
            except Exception:
                pass
            self.page.close(cam_dialog)

        preview_stack = ft.Stack([
            ft.Container(cam_img, border_radius=20, clip_behavior=ft.ClipBehavior.ANTI_ALIAS),
            ft.Container(
                content=filter_label, bgcolor="#00000088", border_radius=10,
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                bottom=10, left=10,
            ),
            rec_indicator,
        ], width=400, height=520)

        bottom_bar = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.PHOTO_LIBRARY, icon_size=32, icon_color=ft.Colors.WHITE,
                    tooltip="Gallery", on_click=open_gallery,
                ),
                ft.Container(
                    content=ft.Container(
                        width=68, height=68, bgcolor=ft.Colors.WHITE,
                        border=ft.border.all(4, "#3A3A46"), border_radius=34, on_click=snap,
                    ),
                    width=90,
                ),
                ft.IconButton(
                    icon=ft.Icons.FIBER_MANUAL_RECORD, icon_size=36, icon_color=ft.Colors.RED_400,
                    tooltip="Record Video", on_click=toggle_recording,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        )

        cam_dialog = ft.AlertDialog(
            content=ft.Container(
                content=ft.Column([
                    preview_stack,
                    ft.Container(height=10),
                    filter_chips,
                    ft.Container(height=10),
                    bottom_bar,
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="#101014", border_radius=20, padding=15,
            ),
            bgcolor="#00000000",
        )
        self.page.open(cam_dialog)

        def camera_loop():
            while running["on"]:
                ret, frame = cap.read()
                if not ret:
                    break
                pil = apply_filter(
                    Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)),
                    current_filter["name"],
                )
                if recording["active"] and recording["writer"] is not None:
                    recording["writer"].write(cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR))
                    rec_timer.value = f"00:{int(time.time() - recording['start']):02d}"
                buf = io.BytesIO()
                pil.save(buf, format="JPEG", quality=40)
                cam_img.src_base64 = base64.b64encode(buf.getvalue()).decode()
                try:
                    self.page.update()
                except Exception:
                    break
                time.sleep(0.066)

        self.page.run_thread(camera_loop)

    def _snack(self, text):
        self.page.snack_bar = ft.SnackBar(ft.Text(text))
        self.page.snack_bar.open = True
        self.page.update()
