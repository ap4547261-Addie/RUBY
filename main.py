# main.py - Ruby V0.2
# Uses: LocalBrain (prompt template) → ResponseEngine (router) → RUBY_PROMPT (personality)

import flet as ft

from brain.local_brain import LocalBrain
from brain.response_engine import ResponseEngine
from prompts.ruby_prompt import RUBY_PROMPT


def main(page: ft.Page):
    page.title = "Ruby v0.2"
    page.padding = 10
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#101014"

    # ----------------------------------------
    # Core
    # ----------------------------------------
    brain = LocalBrain()
    response_engine = ResponseEngine(brain)

    # ----------------------------------------
    # UI Elements
    # ----------------------------------------
    chat = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=10,
    )

    status = ft.Text(
        "🧠 Ruby's brain is not loaded.",
        color=ft.Colors.GREY_400,
        size=12,
    )

    def add_message(sender, message, is_user=False):
        color = ft.Colors.CYAN_400 if is_user else ft.Colors.PINK_400
        chat.controls.append(
            ft.Text(
                f"{sender}: {message}",
                selectable=True,
                size=16,
                color=color,
            )
        )
        page.update()

    # ----------------------------------------
    # File Picker (load GGUF)
    # ----------------------------------------
    def handle_model_result(e: ft.FilePickerResultEvent):
        if not e.files:
            status.value = "No model selected."
            page.update()
            return

        selected = e.files[0]
        status.value = f"🧠 Loading {selected.name}..."
        page.update()

        if not selected.path:
            status.value = "❌ Android did not provide a file path."
            page.update()
            return

        success = brain.load_model(selected.path)

        if success:
            status.value = "🧠 TinyLlama loaded. Ruby is awake!"
            add_message(
                "Ruby",
                "Hyy Addie 😌 I'm awake! My brain is loaded.",
            )
        else:
            status.value = "❌ TinyLlama failed to load."
            page.update()

    file_picker = ft.FilePicker(on_result=handle_model_result)
    page.overlay.append(file_picker)

    def choose_model(e):
        file_picker.pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.ANY,
        )

    # ----------------------------------------
    # Send Message
    # ----------------------------------------
    def send_message(e):
        message = message_box.value.strip()

        if not message:
            return

        message_box.value = ""
        add_message("You", message, is_user=True)

        if not brain.is_loaded():
            add_message("Ruby", "Load my TinyLlama brain first 😭")
            return

        status.value = "💭 Ruby is thinking..."
        page.update()

        response = response_engine.respond(message, RUBY_PROMPT)

        status.value = "🧠 Ruby is ready."
        add_message("Ruby", response)

    # ----------------------------------------
    # Input Row
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

    load_button = ft.ElevatedButton(
        text="🧠 Load TinyLlama",
        icon=ft.Icons.UPLOAD_FILE,
        on_click=choose_model,
    )

    send_button = ft.IconButton(
        icon=ft.Icons.SEND,
        on_click=send_message,
        icon_color=ft.Colors.PINK_400,
    )

    # ----------------------------------------
    # Layout
    # ----------------------------------------
    page.add(
        ft.Text(
            "Ruby",
            size=30,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.PINK_400,
        ),
        status,
        ft.Divider(),
        load_button,
        chat,
        ft.Row(
            controls=[
                message_box,
                send_button,
            ]
        ),
    )

    add_message("Ruby", "Hyy Addie 👀 Load my TinyLlama brain.")


if __name__ == "__main__":
    ft.app(target=main)
