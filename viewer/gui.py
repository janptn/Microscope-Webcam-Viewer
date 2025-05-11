# viewer/gui.py

import customtkinter as ctk
from tkinter import filedialog
from viewer.camera import get_available_cameras, get_supported_resolutions
from viewer.controller import CameraController
from viewer.utils import center_window
from screeninfo import get_monitors


def launch_app():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    root = ctk.CTk()
    AppGUI(root)
    root.mainloop()


class AppGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Microscope Video Viewer 1.0 by Jan Pultin")
        self.controller = CameraController(master)

        center_window(master, 400, 540)
        self.master.resizable(False, False)

        self.build_gui()
        self.master.protocol("WM_DELETE_WINDOW", self.controller.close_all)
        self.master.bind("<F11>", self.controller.toggle_fullscreen)

    def build_gui(self):
        ctk.CTkLabel(self.master, text="Microscope Video Viewer 1.0",
                     font=ctk.CTkFont(size=17, weight="bold", family="Segoe UI")).pack(pady=(15, 5))

        ctk.CTkLabel(self.master, text="Choose Camera:", font=ctk.CTkFont(family="Segoe UI")).pack()
        self.controller.combo = ctk.CTkComboBox(self.master, width=300, state="readonly", font=ctk.CTkFont(family="Segoe UI"))
        self.controller.combo.pack(pady=5)
        self.controller.combo.configure(values=get_available_cameras())
        self.controller.combo.bind("<<ComboboxSelected>>", self.controller.update_resolutions)

        ctk.CTkLabel(self.master, text="Choose Monitor:", font=ctk.CTkFont(family="Segoe UI")).pack()
        self.controller.monitor_combo = ctk.CTkComboBox(self.master, width=300, state="readonly", font=ctk.CTkFont(family="Segoe UI"))
        self.controller.monitor_combo.pack(pady=5)
        self.controller.monitor_combo.configure(
            values=[f"Monitor {i+1} ({m.width}x{m.height})" for i, m in enumerate(get_monitors())]
        )
        self.controller.monitor_combo.set(self.controller.monitor_combo.cget("values")[0])

        ctk.CTkLabel(self.master, text="Choose Resolution:", font=ctk.CTkFont(family="Segoe UI")).pack()
        self.controller.resolution_combo = ctk.CTkComboBox(self.master, width=300, state="readonly", font=ctk.CTkFont(family="Segoe UI"))
        self.controller.resolution_combo.pack(pady=5)
        self.controller.resolution_combo.configure(values=get_supported_resolutions(0))
        self.controller.resolution_combo.set("1920x1080")

        ctk.CTkLabel(self.master, text="Choose FPS:", font=ctk.CTkFont(family="Segoe UI")).pack()
        self.controller.fps_combo = ctk.CTkComboBox(self.master, width=300, state="readonly", font=ctk.CTkFont(family="Segoe UI"))
        self.controller.fps_combo.pack(pady=5)
        self.controller.fps_combo.configure(values=["15", "30", "60"])
        self.controller.fps_combo.set("30")

        button_container = ctk.CTkFrame(self.master)
        button_container.pack(pady=15)

        row1 = ctk.CTkFrame(button_container, fg_color="transparent")
        row1.pack(pady=5)
        row2 = ctk.CTkFrame(button_container, fg_color="transparent")
        row2.pack(pady=10)

        button_width = 140

        ctk.CTkButton(row1, text="Start Camera", width=button_width,
                      font=ctk.CTkFont(family="Segoe UI"), command=self.controller.start_camera).pack(side="left", padx=10)

        ctk.CTkButton(row1, text="Fullscreen", width=button_width,
                      font=ctk.CTkFont(family="Segoe UI"), command=self.controller.toggle_fullscreen).pack(side="left", padx=10)

        ctk.CTkButton(row2, text="Screenshot", width=button_width,
                      font=ctk.CTkFont(family="Segoe UI"), command=self.controller.take_screenshot).pack(side="left", padx=10)

        ctk.CTkButton(row2, text="Set Save Folder", width=button_width,
                      font=ctk.CTkFont(family="Segoe UI"), command=self.controller.set_screenshot_path).pack(side="left", padx=10)

        ctk.CTkLabel(self.master, text="Use mouse wheel in camera window to zoom",
                     font=ctk.CTkFont(size=10, family="Segoe UI")).pack(pady=(5, 2))

        ctk.CTkLabel(self.master, text="by Jan Pultin",
                     font=ctk.CTkFont(size=10, family="Segoe UI")).pack(pady=(0, 10))
