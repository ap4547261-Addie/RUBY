# main.py - Ruby V1.9
import os
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import shutil
import asyncio
import re
import flet as ft

from brain.local_brain import LocalBrain
from brain.response_engine import ResponseEngine
from brain.system1 import System1
from brain.system2 import System2
from prompts.ruby_prompt import build_ruby_prompt
from settings.settings_manager import SettingsManager
from tools.ws_server import WSServer
from cognition.curiosity import Curiosity
from brain.brain_monitor import BrainMonitor


def main(page: ft.Page):
    page.title = "Ruby"
    page.padding = 10
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#101014"

    # ----------------------------------------
    # Core
    # ----------------------------------------
    brain = LocalBrain()
    settings = SettingsManager()
    curiosity = Curiosity()

    user_name = settings.get("user_name", "not_set")

    response_engine = ResponseEngine(
        brain,
        user_name=user_name,
        platform="private",
        curiosity=curiosity
    )

    system1 = System1(user_name=user_name)
    system2 = System2(response_engine, ruby_prompt="")

    brain_monitor = BrainMonitor()

    # ----------------------------------------
    # UI
    # ----------------------------------------
    chat = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=10)
    status = ft.Text("🧠 Ruby's brain is not loaded.", color=ft.Colors.GREY_400, size=12)
    ws_status = ft.Text("🔌 Extension: not connected", size=11, color=ft.Colors.GREY_500)

    file_picker_mode = {"action": None}

    def add_message(sender, message, is_user=False):
        color = ft.Colors.CYAN_400 if is_user else ft.Colors.PINK_400
        chat.controls.append(
            ft.Text(f"{sender}: {message}", selectable=True, size=16, color=color)
        )
        page.update()

    def show_snack(text):
        page.snack_bar = ft.SnackBar(ft.Text(text))
        page.snack_bar.open = True
        page.update()

    # ----------------------------------------
    # Load chat history
    # ----------------------------------------
    def load_chat_history():
        try:
            from memory.episodic_memory import EpisodicMemory
            ep = EpisodicMemory()
            rows = ep.get_recent(limit=200)
            for user_msg, ruby_reply, _ts in reversed(rows):
                chat.controls.append(
                    ft.Text(f"You: {user_msg}", selectable=True, size=16, color=ft.Colors.CYAN_400)
                )
                chat.controls.append(
                    ft.Text(f"Ruby: {ruby_reply}", selectable=True, size=16, color=ft.Colors.PINK_400)
                )
            if rows:
                print(f"📜 Restored {len(rows)} past exchanges.")
        except Exception as ex:
            print(f"⚠️ Could not load chat history: {ex}")

    # ----------------------------------------
    # Stable model path
    # ----------------------------------------
    def get_stable_model_path(original_path, original_name):
        storage_dir = os.getenv("FLET_APP_STORAGE_DATA", ".")
        stable_dir = os.path.join(storage_dir, "models")
        os.makedirs(stable_dir, exist_ok=True)
        stable_path = os.path.join(stable_dir, original_name)

        try:
            if os.path.abspath(original_path) == os.path.abspath(stable_path):
                return stable_path
        except Exception:
            pass

        if os.path.exists(stable_path):
            return stable_path

        try:
            print(f"📦 Copying model to permanent storage: {stable_path}")
            shutil.copy(original_path, stable_path)
            print("✅ Model copied.")
            return stable_path
        except Exception as e:
            print(f"⚠️ Copy failed, using original path: {e}")
            return original_path

    # ----------------------------------------
    # Model Loading
    # ----------------------------------------
    def load_model(path, name):
        try:
            status.value = f"🧠 Loading {name}..."
            page.update()

            stable_path = get_stable_model_path(path, name)
            success = brain.load_model(stable_path)

            if success:
                status.value = f"🧠 {name} loaded. Ruby is awake!"
                settings.set("model_path", stable_path)
                settings.set("model_name", name)
            else:
                status.value = f"❌ Failed to load {name}"
            page.update()
        except Exception as e:
            print(f"❌ load_model error: {e}")
            status.value = f"❌ {e}"
            page.update()

    # ----------------------------------------
    # File Picker
    # ----------------------------------------
    def handle_file_pick(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        f = e.files[0]
        if not f.path:
            status.value = "❌ No file path provided."
            page.update()
            return

        action = file_picker_mode.get("action")
        if action == "model":
            load_model(f.path, f.name)
        elif action == "import_backup":
            ok = settings.import_backup(f.path)
            if ok:
                show_snack("✅ Backup imported. Restart the app to apply.")
            else:
                show_snack("❌ Backup import failed.")
        file_picker_mode["action"] = None

    file_picker = ft.FilePicker(on_result=handle_file_pick)
    page.overlay.append(file_picker)

    # ----------------------------------------
    # WebSocket bridge
    # ----------------------------------------
    async def ws_handler(msg):
        platform = msg.get("platform", "unknown")
        content = msg.get("content", "")
        url = msg.get("url", "")
        result = response_engine.ingest_extension_content(platform, url, content)
        return {
            "ok": result.get("ok", False),
            "extra": {"platform": platform, "new": result.get("is_new")},
        }

    ws_server = WSServer(handler=ws_handler)

    def _on_connect(n):
        ws_status.value = f"🔌 Extension connected ({n})"
        ws_status.color = ft.Colors.GREEN_400
        page.update()

    def _on_disconnect(n):
        ws_status.value = "🔌 Extension: not connected"
        ws_status.color = ft.Colors.GREY_500
        page.update()

    def _on_message(platform, n_chars):
        ws_status.value = f"📨 Got {n_chars} chars from {platform}"
        ws_status.color = ft.Colors.CYAN_400
        page.update()

    ws_server.on_connect = _on_connect
    ws_server.on_disconnect = _on_disconnect
    ws_server.on_message = _on_message

    # ----------------------------------------
    # Settings Dialog (unchanged, keep as-is)
    # ----------------------------------------
    def open_settings(e):
        # ... KEEP YOUR EXISTING open_settings CODE EXACTLY AS IT WAS ...
        # (paste your full existing function here — I'm not touching it)
        pass  # <-- REPLACE THIS with your existing open_settings function body

    # ----------------------------------------
    # Send Message
    # ----------------------------------------
    async def send_message(e):
        msg = message_box.value.strip()
        if not msg:
            return
        message_box.value = ""
        add_message("You", msg, is_user=True)

        if not brain.is_loaded():
            add_message("Ruby", "Load my brain first 😭 (⚙️)")
            return

        interaction_depth = max(1, len(chat.controls) // 2)
        base_prompt = build_ruby_prompt(interaction_depth=interaction_depth)

        route = system1.classify(msg)
        print(f"🧭 System1 route: {route}")

        if route == "trivial":
            status.value = "💭 ..."
        elif route == "deep":
            status.value = "💭 thinking deeply..."
        else:
            status.value = "💭 Ruby is thinking..."
        page.update()

        try:
            system2.ruby_prompt = base_prompt

            if route == "trivial":
                reply = await asyncio.to_thread(
                    response_engine.respond_fast, msg, base_prompt
                )
            else:
                reply = await asyncio.to_thread(
                    system2.think, msg, route
                )
        except Exception as ex:
            reply = f"⚠️ error: {ex}"
            print(f"❌ respond error: {ex}")

        status.value = "🧠 Ruby is ready."

        # ============================================================
        # 📸 SELFIE TOKEN PARSER
        # ============================================================
        selfie_match = re.search(r"\[SEND_SELFIE:\s*([^\]]+)\]", reply)
        if selfie_match:
            filter_name = selfie_match.group(1).strip()
            # Remove the token from her spoken text
            spoken = re.sub(r"\[SEND_SELFIE:[^\]]+\]", "", reply).strip()
            add_message("Ruby", spoken)

            try:
                from PIL import Image
                from tools.snapchat_filters import apply_filter, FILTERS

                # Normalize filter name (case-insensitive match)
                matched = None
                for f in FILTERS:
                    if f.lower() == filter_name.lower():
                        matched = f
                        break
                chosen = matched if matched else "none"

                # Find reference photo
                base_path = None
                for cand in [
                    "ruby_base.jpg", "ruby_base.png",
                    "RUBY/RUBY_03.png", "RUBY/RUBY_03.jpg",
                ]:
                    if os.path.exists(cand):
                        base_path = cand
                        break

                if base_path:
                    base_img = Image.open(base_path).convert("RGB")
                    filtered = apply_filter(base_img, chosen)
                    os.makedirs("ruby_selfies", exist_ok=True)
                    out_path = f"ruby_selfies/ruby_{chosen.replace(' ', '_')}.jpg"
                    filtered.save(out_path, quality=90)
                    chat.controls.append(
                        ft.Image(src=out_path, width=300, height=300, border_radius=10)
                    )
                    print(f"📸 Selfie sent with filter: {chosen}")
                else:
                    print(f"⚠️ No reference photo found for selfie.")
            except Exception as ex:
                print(f"⚠️ Selfie generation error: {ex}")
        else:
            add_message("Ruby", reply)
        # ============================================================
        # END SELFIE PARSER
        # ============================================================

        # Save curiosity memory
        try:
            curiosity.save_memory()
        except Exception as e:
            print(f"⚠️ Failed to save curiosity memory: {e}")

        # Update Brain Monitor
        try:
            brain_state = response_engine.get_brain_state()
            for region, value in brain_state.items():
                brain_monitor.update_ui(region, value)
            page.update()
        except Exception as ex:
            print(f"⚠️ Failed to update brain monitor: {ex}")

    # ----------------------------------------
    # Layout
    # ----------------------------------------
    message_box = ft.TextField(
        hint_text="Talk to Ruby...", expand=True, multiline=False,
        on_submit=send_message, bgcolor="#18181C", color=ft.Colors.WHITE,
        border_color="#3A3A46", focused_border_color=ft.Colors.PINK_400,
    )
    settings_button = ft.IconButton(
        icon=ft.Icons.SETTINGS, on_click=open_settings,
        icon_color=ft.Colors.GREY_400, tooltip="Settings",
    )
    send_button = ft.IconButton(
        icon=ft.Icons.SEND, on_click=send_message,
        icon_color=ft.Colors.PINK_400,
    )

    main_chat_ui = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Text("Ruby", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.PINK_400),
                    settings_button,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            status,
            ws_status,
            ft.Divider(),
            chat,
            ft.Row(controls=[message_box, send_button]),
        ],
        expand=True,
    )

    sidebar_ui = ft.Container(
        content=brain_monitor.get_ui(),
        width=280,
        padding=10,
        bgcolor="#18181C",
        border_radius=10,
        border=ft.border.all(1, "#3A3A46"),
        margin=ft.margin.only(left=10)
    )

    page.add(
        ft.Row(
            controls=[main_chat_ui, sidebar_ui],
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START
        )
    )

    load_chat_history()
    page.update()

    page.run_task(ws_server.serve)

    if settings.has_model():
        print(f"📂 Auto-loading: {settings.get('model_name')}")

        async def _auto_load_model():
            path = settings.get("model_path")
            name = settings.get("model_name")
            try:
                await asyncio.to_thread(load_model, path, name)
            except Exception as e:
                print(f"❌ Auto-load failed: {e}")

        page.run_task(_auto_load_model)
    else:
        status.value = "🧠 No model selected. Tap ⚙️ to choose one."
        page.update()


if __name__ == "__main__":
    ft.app(target=main)
