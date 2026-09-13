import flet as ft

from brain.local_brain import LocalBrain
from brain.response_engine import ResponseEngine
from prompts.ruby_prompt import RUBY_PROMPT


def main(page: ft.Page):
    page.title = "Ruby v0.1"
    page.padding = 10
    page.theme_mode = ft.ThemeMode.DARK

    # Ruby's brain
    brain = LocalBrain()
    response_engine = ResponseEngine(brain)

    # -----------------------------
    # Chat area
    # -----------------------------

    chat = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=10,
    )

    # -----------------------------
    # Status
    # -----------------------------

    status = ft.Text(
        "🧠 Ruby's brain is not loaded.",
        size=14,
    )

    # -----------------------------
    # Message box
    # -----------------------------

    message_box = ft.TextField(
        hint_text="Talk to Ruby...",
        expand=True,
        multiline=False,
        on_submit=lambda e: send_message(e),
    )

    # -----------------------------
    # Add chat message
    # -----------------------------

    def add_message(sender, message):
        chat.controls.append(
            ft.Text(
                f"{sender}: {message}",
                selectable=True,
                size=16,
            )
        )

        page.update()

    # -----------------------------
    # File picker
    # -----------------------------

    async def model_picker_result(e: ft.FilePickerResultEvent):
        if not e.files:
            return

        selected_file = e.files[0]

        status.value = "🧠 Loading TinyLlama..."
        page.update()

        success = brain.load_model(selected_file.path)

        if success:
            status.value = "🧠 TinyLlama loaded. Ruby is awake!"
            add_message(
                "Ruby",
                "Hyy Addie 😌 I'm awake. My brain is loaded!",
            )
        else:
            status.value = "❌ TinyLlama failed to load."
            page.update()

    file_picker = ft.FilePicker(
        on_result=model_picker_result
    )

    page.overlay.append(file_picker)

    # -----------------------------
    # Open model picker
    # -----------------------------

    async def choose_model(e):
        await file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["gguf"],
        )

    # -----------------------------
    # Send message
    # -----------------------------

    def send_message(e):
        message = message_box.value.strip()

        if not message:
            return

        message_box.value = ""

        add_message(
            "You",
            message,
        )

        if not brain.is_loaded():
            add_message(
                "Ruby",
                "You need to load my TinyLlama brain first 😭",
            )
            return

        status.value = "💭 Ruby is thinking..."
        page.update()

        response = response_engine.respond(
            message,
            RUBY_PROMPT,
        )

        status.value = "🧠 Ruby is ready."
        add_message(
            "Ruby",
            response,
        )

    # -----------------------------
    # Buttons
    # -----------------------------

    load_button = ft.ElevatedButton(
        text="🧠 Load TinyLlama",
        icon=ft.Icons.UPLOAD_FILE,
        on_click=choose_model,
    )

    send_button = ft.IconButton(
        icon=ft.Icons.SEND,
        on_click=send_message,
    )

    # -----------------------------
    # UI
    # -----------------------------

    page.add(
        ft.Text(
            "Ruby",
            size=30,
            weight=ft.FontWeight.BOLD,
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

    # -----------------------------
    # Startup message
    # -----------------------------

    add_message(
        "Ruby",
        "Hyy Addie 👀 Load my TinyLlama brain and let's talk.",
    )


ft.app(target=main)
