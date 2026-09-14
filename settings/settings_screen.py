import flet as ft


def open_settings(page: ft.Page, settings, on_model_pick, file_picker):
    """
    Opens the settings dialog.
    page: the Flet page
    settings: SettingsManager instance
    on_model_pick: callback fired when user taps "Choose Model File"
    file_picker: FilePicker instance
    """

    # -------------------------
    # Account fields
    # -------------------------
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

    # -------------------------
    # Brain fields
    # -------------------------
    model_label = ft.Text(
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

    # -------------------------
    # Backup label
    # -------------------------
    last_backup = settings.get("last_backup") or "Never"
    backup_label = ft.Text(
        f"Last backup: {last_backup}",
        size=12, color=ft.Colors.GREY_400,
    )

    # -------------------------
    # Actions
    # -------------------------
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
        page.close(dialog)
        page.update()

    def pick_model(ev):
        page.close(dialog)
        on_model_pick()

    def do_backup(ev):
        path = settings.export_backup()
        if path:
            backup_label.value = f"✅ Backup saved: {path}"
        else:
            backup_label.value = "❌ Backup failed"
        page.update()

    def pick_restore_file(ev):
        file_picker.pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.ANY,
        )

    # -------------------------
    # Dialog
    # -------------------------
    dialog = ft.AlertDialog(
        title=ft.Text("⚙️ Settings"),
        content=ft.Column(
            [
                # Account
                ft.Text("👤 Account", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.PINK_400),
                name_field,
                phone_field,
                email_field,
                ft.ElevatedButton("🔐 Sign in with Google", disabled=True, width=340),
                ft.Divider(),

                # Brain
                ft.Text("🧠 Brain", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.PINK_400),
                model_label,
                ft.ElevatedButton(
                    "Choose Model File",
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=pick_model,
                    width=340,
                ),
                context_field,
                threads_field,
                ft.Divider(),

                # Backup
                ft.Text("💾 Backup", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.PINK_400),
                backup_label,
                ft.Row(
                    [
                        ft.ElevatedButton("Export", icon=ft.Icons.DOWNLOAD, on_click=do_backup),
                        ft.ElevatedButton("Import", icon=ft.Icons.UPLOAD, on_click=pick_restore_file),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Divider(),

                # Integrations
                ft.Text("🔗 Integrations", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.PINK_400),
                ft.Text("Pinecone: Not connected", size=13, color=ft.Colors.GREY_400),
                ft.Text("Instagram: Not connected", size=13, color=ft.Colors.GREY_400),
            ],
            tight=True, spacing=10, width=360,
            scroll=ft.ScrollMode.AUTO,
        ),
        actions=[
            ft.TextButton("Save", on_click=save_and_close),
            ft.TextButton("Close", on_click=lambda ev: page.close(dialog)),
        ],
    )

    page.open(dialog)
