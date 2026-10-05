import flet as ft

class BrainMonitor:
    def __init__(self):
        self.controls = {}
        self.regions = ["cortex", "thalamus", "hippocampus", "amygdala", "global_workspace", "decision"]
        
        for region in self.regions:
            self.controls[region] = ft.ProgressBar(
                value=0.0, 
                color=ft.Colors.PINK_400 if region == "amygdala" else ft.Colors.CYAN_400,
                bgcolor="#18181C"
            )
            
    def get_ui(self):
        return ft.Column([
            ft.Text("🧠 Live Brain Monitor", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.PINK_400),
            *[ft.Row([ft.Text(r.capitalize(), size=12, width=100), self.controls[r]]) for r in self.regions]
        ], spacing=5)

    def update_ui(self, node, value):
        if node in self.controls:
            self.controls[node].value = value
