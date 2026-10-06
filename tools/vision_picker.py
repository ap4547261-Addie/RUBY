# tools/vision_picker.py
import os
import asyncio
import flet as ft

from tools.vision import caption_image, caption_video


IMAGE_EXTS = [".jpg", ".jpeg", ".png", ".webp", ".bmp"]
VIDEO_EXTS = [".mp4", ".mov", ".avi", ".mkv", ".webm"]


class VisionPicker:
    """Handles media uploads: pick → display → caption → send to Ruby's brain."""

    def __init__(self, page: ft.Page, chat_column, add_message_fn, status_fn, send_to_brain_fn):
        self.page = page
        self.chat = chat_column
        self.add_message = add_message_fn
        self.set_status = status_fn
        self.send_to_brain = send_to_brain_fn  # async function
        self.picker = ft.FilePicker(on_result=self._on_result)
        self.page.overlay.append(self.picker)

    def open(self):
        self.picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.ANY)

    def _on_result(self, e: ft.FilePickerResultEvent):
        if not e.files:
            return
        f = e.files[0]
        if not f.path:
            return
        # 🔥 FIX: Use page.run_task() instead of asyncio.create_task().
        # Flet's page.run_task schedules the coroutine on the event loop
        # that Flet itself manages — this works from sync callbacks.
        self.page.run_task(self._handle_file, f.path)

    async def _handle_file(self, path: str):
        ext = os.path.splitext(path)[1].lower()
        filename = os.path.basename(path)

        # Show the user's upload in the chat
        if ext in IMAGE_EXTS:
            self.chat.controls.append(
                ft.Image(src=path, width=280, height=280, fit=ft.ImageFit.COVER, border_radius=10)
            )
        elif ext in VIDEO_EXTS:
            self.chat.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.PLAY_CIRCLE_FILLED, color=ft.Colors.PINK_400, size=32),
                        ft.Text(f"🎥 {filename}", color=ft.Colors.CYAN_300, size=13),
                    ]),
                    bgcolor="#18181C", border_radius=10, padding=10,
                )
            )
        else:
            self.add_message("You", f"[Sent: {filename}]", is_user=True)
            self.set_status("❌ Unsupported file type.")
            self.page.update()
            return

        self.page.update()

        # Caption the file
        self.set_status("👁️ Ruby is looking at it...")
        self.page.update()

        try:
            if ext in IMAGE_EXTS:
                description = await asyncio.to_thread(caption_image, path)
                prompt = f"[The user sent you an image. You see: '{description}']"
            else:
                description = await asyncio.to_thread(caption_video, path)
                prompt = f"[The user sent you a video. You see across the sampled frames:\n{description}\n]"

            print(f"👁️ Vision result: {prompt[:200]}...")

            # Send to Ruby's brain for a natural reply
            await self.send_to_brain(prompt)

        except Exception as ex:
            print(f"❌ Vision picker error: {ex}")
            self.add_message("Ruby", f"Something went wrong with that file.")
        finally:
            self.set_status("🧠 Ruby is ready.")
            self.page.update()
