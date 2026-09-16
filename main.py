# main.py - Ruby V0.6 (Memory + Internal State + Emotion)

import os
import shutil
import flet as ft

from brain.local_brain import LocalBrain
from brain.response_engine import ResponseEngine
from prompts.ruby_prompt import RUBY_PROMPT
from settings.settings_manager import SettingsManager


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

    user_name = settings.get("user_name", "not_set")
    response_engine = ResponseEngine(brain, user_name=user_name)

    # ----------------------------------------
    # UI
    # ----------------------------------------
    chat = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=10)
    status = ft.Text("🧠 Ruby's brain is not loaded.", color=ft.Colors.GREY_400, size=12)

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
    # Load chat history on startup
    # ----------------------------------------
    def load_chat_history():
        try:
            from memory.episodic_memory import EpisodicMemory
            ep = EpisodicMemory()
            rows = ep.get_recent(limit=30)
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
    # Settings Dialog
    # ----------------------------------------
    def open_settings(e):
        # --- Account fields ---
        name_field = ft.TextField(
            label="Name",
            value=settings.get("user_name", ""),
            bgcolor="#18181C", color=ft.Colors.WHITE, border_color="#3A3A46",
        )
        phone_field = ft.TextField(
            label="Phone Number",
            value=settings.get("user_phone", ""),
            keyboard_type=ft.KeyboardType.PHONE,
            bgcolor="#18181C", color=ft.Colors.WHITE, border_color="#3A3A46",
        )
        email_field = ft.TextField(
            label="Email",
            value=settings.get("user_email", ""),
            keyboard_type=ft.KeyboardType.EMAIL,
            bgcolor="#18181C", color=ft.Colors.WHITE, border_color="#3A3A46",
        )

        # --- Brain fields ---
        model_name_label = ft.Text(
            settings.get("model_name") or "No model selected",
            size=13, color=ft.Colors.GREY_400,
        )
        context_field = ft.TextField(
            label="Context Size",
            value=str(settings.get("context_size", 1024)),
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor="#18181C", color=ft.Colors.WHITE, border_color="#3A3A46",
        )
        threads_field = ft.TextField(
            label="Threads",
            value=str(settings.get("threads", 4)),
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor="#18181C", color=ft.Colors.WHITE, border_color="#3A3A46",
        )

        # --- Backup label ---
        last_backup = settings.get("last_backup") or "Never"
        backup_label = ft.Text(
            f"Last backup: {last_backup}",
            size=12, color=ft.Colors.GREY_400,
        )

        # --- Memory stats (V0.4) ---
        try:
            stats = response_engine.memory_stats()
            rel = stats["relationship"]
            mem_episodes = ft.Text(f"Episodes: {stats['episodes']}", size=12, color=ft.Colors.GREY_400)
            mem_facts = ft.Text(f"Facts: {stats['facts']}", size=12, color=ft.Colors.GREY_400)
            mem_msgs = ft.Text(f"Messages: {rel['message_count']}", size=12, color=ft.Colors.GREY_400)
            mem_trust = ft.Text(f"Trust: {rel['trust']}", size=12, color=ft.Colors.GREY_400)
            mem_fam = ft.Text(f"Familiarity: {rel['familiarity']}", size=12, color=ft.Colors.GREY_400)
            mem_resp = ft.Text(f"Respect: {rel['respect']}", size=12, color=ft.Colors.GREY_400)
            mem_att = ft.Text(f"Attachment: {rel['attachment']}", size=12, color=ft.Colors.GREY_400)
        except Exception as ex:
            mem_episodes = ft.Text(f"Memory unavailable: {ex}", size=12, color=ft.Colors.RED_300)
            mem_facts = ft.Text("", size=12)
            mem_msgs = ft.Text("", size=12)
            mem_trust = ft.Text("", size=12)
            mem_fam = ft.Text("", size=12)
            mem_resp = ft.Text("", size=12)
            mem_att = ft.Text("", size=12)

        # --- Internal State (V0.5) ---
        try:
            inner_data = response_engine.internal_state_stats()
            inner_energy = ft.Text(f"Energy: {inner_data['energy']}", size=12, color=ft.Colors.CYAN_300)
            inner_warmth = ft.Text(f"Warmth: {inner_data['warmth']}", size=12, color=ft.Colors.CYAN_300)
            inner_tension = ft.Text(f"Tension: {inner_data['tension']}", size=12, color=ft.Colors.CYAN_300)
            inner_irrit = ft.Text(f"Irritation: {inner_data['irritation']}", size=12, color=ft.Colors.CYAN_300)
        except Exception as inner_ex:
            inner_energy = ft.Text(f"State unavailable: {inner_ex}", size=12, color=ft.Colors.RED_300)
            inner_warmth = ft.Text("", size=12)
            inner_tension = ft.Text("", size=12)
            inner_irrit = ft.Text("", size=12)

        # --- Emotions (V0.6) ---
        try:
            emo = response_engine.emotion_stats()
            # show only emotions that have actually fired (> 0.1)
            active = {k: v for k, v in emo.items() if v > 0.1}
            if active:
                # sort descending by intensity
                sorted_emo = sorted(active.items(), key=lambda x: -x[1])
                emo_lines = [
                    ft.Text(f"{k}: {v}", size=12, color=ft.Colors.PURPLE_200)
                    for k, v in sorted_emo
                ]
            else:
                emo_lines = [ft.Text("No active emotions yet.", size=12, color=ft.Colors.GREY_500)]
        except Exception as emo_ex:
            emo_lines = [ft.Text(f"Emotions unavailable: {emo_ex}", size=12, color=ft.Colors.RED_300)]

        # --- Actions ---
        def pick_model(ev):
            page.close(settings_dialog)
            file_picker_mode["action"] = "model"
            file_picker.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.ANY,
            )

        def save_and_close(ev):
            try:
                ctx = int(context_field.value or 1024)
                thr = int(threads_field.value or 4)
            except ValueError:
                ctx, thr = 1024, 4

            settings.update({
                "user_name": name_field.value.strip() or "not_set",
                "user_phone": phone_field.value.strip(),
                "user_email": email_field.value.strip(),
                "context_size": ctx,
                "threads": thr,
            })
            status.value = "✅ Settings saved. Restart to apply name change."
            page.close(settings_dialog)
            page.update()

        def do_export(ev):
            path = settings.export_backup()
            if path:
                backup_label.value = f"✅ Saved: {path}"
                show_snack("✅ Backup exported to Downloads/ruby_backups/")
            else:
                backup_label.value = "❌ Export failed"
            page.update()

        def do_import(ev):
            page.close(settings_dialog)
            file_picker_mode["action"] = "import_backup"
            file_picker.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.ANY,
            )

        def do_wipe_memory(ev):
            try:
                response_engine.wipe_all_memory()
                mem_episodes.value = "Episodes: 0"
                mem_facts.value = "Facts: 0"
                mem_msgs.value = "Messages: 0"
                mem_trust.value = "Trust: 0"
                mem_fam.value = "Familiarity: 0"
                mem_resp.value = "Respect: 0"
                mem_att.value = "Attachment: 0"
                inner_energy.value = "Energy: 0.0"
                inner_warmth.value = "Warmth: 0.0"
                inner_tension.value = "Tension: 0.0"
                inner_irrit.value = "Irritation: 0.0"
                chat.controls.clear()
                show_snack("🗑️ All memory wiped.")
            except Exception as ex:
                show_snack(f"❌ Wipe failed: {ex}")
            page.update()

        # --- Dialog ---
        settings_dialog = ft.AlertDialog(
            title=ft.Text("⚙️ Settings"),
            content=ft.Column(
                [
                    # --- Account ---
                    ft.Text("👤 Account", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.PINK_400),
                    name_field,
                    phone_field,
                    email_field,
                    ft.ElevatedButton("🔐 Sign in with Google", disabled=True, width=340),
                    ft.Divider(),

                    # --- Brain ---
                    ft.Text("🧠 Brain", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.PINK_400),
                    model_name_label,
                    ft.ElevatedButton(
                        "Choose Model File",
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=pick_model,
                        width=340,
                    ),
                    context_field,
                    threads_field,
                    ft.Divider(),

                    # --- Memory (V0.4) ---
                    ft.Text("💭 Memory", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.PINK_400),
                    mem_episodes,
                    mem_facts,
                    mem_msgs,
                    mem_trust,
                    mem_fam,
                    mem_resp,
                    mem_att,
                    ft.Divider(),

                    # --- Internal State (V0.5) ---
                    ft.Text("🧬 Internal State", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.CYAN_300),
                    inner_energy,
                    inner_warmth,
                    inner_tension,
                    inner_irrit,
                    ft.Divider(),

                    # --- Emotions (V0.6) ---
                    ft.Text("❤️ Emotions", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.PURPLE_200),
                    *emo_lines,
                    ft.Divider(),

                    # --- Wipe ---
                    ft.ElevatedButton(
                        "Wipe All Memory",
                        icon=ft.Icons.DELETE_FOREVER,
                        on_click=do_wipe_memory,
                        width=340,
                    ),
                    ft.Divider(),

                    # --- Backup ---
                    ft.Text("💾 Backup", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.PINK_400),
                    backup_label,
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Export",
                                icon=ft.Icons.DOWNLOAD,
                                on_click=do_export,
                            ),
                            ft.ElevatedButton(
                                "Import",
                                icon=ft.Icons.UPLOAD,
                                on_click=do_import,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Divider(),

                    # --- Integrations ---
                    ft.Text("🔗 Integrations", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.PINK_400),
                    ft.Text("Pinecone: Not connected", size=13, color=ft.Colors.GREY_400),
                    ft.Text("Instagram: Not connected", size=13, color=ft.Colors.GREY_400),
                ],
                tight=True,
                spacing=10,
                width=360,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton("Save", on_click=save_and_close),
                ft.TextButton("Close", on_click=lambda ev: page.close(settings_dialog)),
            ],
        )
        page.open(settings_dialog)

    # ----------------------------------------
    # Send Message
    # ----------------------------------------
    def send_message(e):
        msg = message_box.value.strip()
        if not msg:
            return

        message_box.value = ""
        add_message("You", msg, is_user=True)

        if not brain.is_loaded():
            add_message("Ruby", "Load my brain first 😭 (⚙️)")
            return

        status.value = "💭 Ruby is thinking..."
        page.update()

        try:
            reply = response_engine.respond(msg, RUBY_PROMPT)
        except Exception as ex:
            reply = f"⚠️ error: {ex}"
            print(f"❌ respond error: {ex}")

        status.value = "🧠 Ruby is ready."
        add_message("Ruby", reply)

    # ----------------------------------------
    # Layout
    # ----------------------------------------
    message_box = ft.TextField(
        hint_text="Talk to Ruby...",
        expand=True,
        multiline=False,
        on_submit=send_message,
        bgcolor="#18181C",
        color=ft.Colors.WHITE,
        border_color="#3A3A46",
        focused_border_color=ft.Colors.PINK_400,
    )

    settings_button = ft.IconButton(
        icon=ft.Icons.SETTINGS,
        on_click=open_settings,
        icon_color=ft.Colors.GREY_400,
        tooltip="Settings",
    )

    send_button = ft.IconButton(
        icon=ft.Icons.SEND,
        on_click=send_message,
        icon_color=ft.Colors.PINK_400,
    )

    page.add(
        ft.Row(
            controls=[
                ft.Text("Ruby", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.PINK_400),
                settings_button,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        status,
        ft.Divider(),
        chat,
        ft.Row(controls=[message_box, send_button]),
    )

    # ----------------------------------------
    # Restore previous chat + auto-load model
    # ----------------------------------------
    load_chat_history()
    page.update()

    if settings.has_model():
        print(f"📂 Auto-loading: {settings.get('model_name')}")
        load_model(settings.get("model_path"), settings.get("model_name"))
    else:
        status.value = "🧠 No model selected. Tap ⚙️ to choose one."
        page.update()


if __name__ == "__main__":
    ft.app(target=main)
