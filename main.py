# main.py - Ruby with Settings + Backup

import flet as ft

from brain.local_brain import LocalBrain
from brain.response_engine import ResponseEngine
from personality.ruby import RUBY_PROMPT
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
    response_engine = ResponseEngine(brain)
    settings = SettingsManager()

    # ----------------------------------------
    # UI
    # ----------------------------------------
    chat = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=10)
    status = ft.Text("🧠 Ruby's brain is not loaded.", color=ft.Colors.GREY_400, size=12)

    # Tracks what the file picker should do next
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
    # Model Loading
    # ----------------------------------------
    def load_model(path, name):
        status.value = f"🧠 Loading {name}..."
        page.update()

        success = brain.load_model(path)
        if success:
            status.value = f"🧠 {name} loaded. Ruby is awake!"
            settings.set("model_path", path)
            settings.set("model_name", name)
            add_message("Ruby", "Hyy Addie 😌 I'm awake!")
        else:
            status.value = f"❌ Failed to load {name}"
            page.update()

    # ----------------------------------------
    # File Picker (handles both .gguf and .json)
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
                "user_name": name_field.value.strip() or "Addie",
                "user_phone": phone_field.value.strip(),
                "user_email": email_field.value.strip(),
                "context_size": ctx,
                "threads": thr,
            })
            status.value = "✅ Settings saved."
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

        reply = response_engine.respond(msg, RUBY_PROMPT)

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

    add_message("Ruby", "Hyy Addie 👀 Ready when you are.")

    # ----------------------------------------
    # Auto-load saved model
    # ----------------------------------------
    if settings.has_model():
        print(f"📂 Auto-loading: {settings.get('model_name')}")
        load_model(settings.get("model_path"), settings.get("model_name"))
    else:
        status.value = "🧠 No model selected. Tap ⚙️ to choose one."
        page.update()


if __name__ == "__main__":
    ft.app(target=main)
