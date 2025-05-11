# viewer/gui.py

import customtkinter as ctk
from tkinter import filedialog
from viewer.camera import get_available_cameras, get_supported_resolutions
from viewer.controller import CameraController
from viewer.utils import center_window
from screeninfo import get_monitors
import cv2
import threading


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

        center_window(master, 400, 580)
        self.master.resizable(False, False)

        self.build_gui()
        self.master.protocol("WM_DELETE_WINDOW", self.controller.close_all)
        self.master.bind("<F11>", self.controller.toggle_fullscreen)

    def build_gui(self):
        # Titel
        ctk.CTkLabel(self.master,
                     text="Microscope Video Viewer 1.0",
                     font=ctk.CTkFont(size=17, weight="bold", family="Segoe UI")
                     ).pack(pady=(15, 5))

        # Kameraauswahl
        ctk.CTkLabel(self.master,
                     text="Choose Camera:",
                     font=ctk.CTkFont(family="Segoe UI")
                     ).pack()
        cam_row = ctk.CTkFrame(self.master)
        cam_row.pack(pady=5)

        self.controller.combo = ctk.CTkComboBox(
            cam_row,
            width=250, state="readonly", font=ctk.CTkFont(family="Segoe UI"))
        self.controller.combo.pack(side="left", padx=(0,10))
        self.controller.combo.configure(values=get_available_cameras())
        # Erstinitialisierung
        if self.controller.combo.cget("values"):
            self.controller.combo.set(self.controller.combo.cget("values")[0])
        # Auswahl-Ereignis
        self.controller.combo.bind("<<ComboboxSelected>>", lambda e: self.on_camera_selected())

        
        # Refresh-Kamera Button
        refresh_cam_btn = ctk.CTkButton(
            cam_row,
            text="⟳",
            width=35,
            command=self.refresh_cameras
        )
        refresh_cam_btn.pack(side="left")

        # Monitorauswahl
        ctk.CTkLabel(self.master,
                     text="Choose Monitor:",
                     font=ctk.CTkFont(family="Segoe UI")
                     ).pack()
        self.controller.monitor_combo = ctk.CTkComboBox(
            self.master,
            width=300,
            state="readonly",
            font=ctk.CTkFont(family="Segoe UI")
        )
        self.controller.monitor_combo.pack(pady=5)
        self.controller.monitor_combo.configure(
            values=[f"Monitor {i+1} ({m.width}x{m.height})" for i, m in enumerate(get_monitors())]
        )
        self.controller.monitor_combo.set(self.controller.monitor_combo.cget("values")[0])

                        # Settings grid (2x2): Resolution, FPS, Codec, Refresh Settings
        settings_frame = ctk.CTkFrame(self.master)
        settings_frame.pack(pady=10)

        # Resolution label and dropdown
        ctk.CTkLabel(settings_frame, text="Resolution:", font=ctk.CTkFont(family="Segoe UI")).grid(row=0, column=0, padx=5, pady=(5,2), sticky="w")
        self.controller.resolution_combo = ctk.CTkComboBox(
            settings_frame,
            width=140,
            state="readonly",
            font=ctk.CTkFont(family="Segoe UI")
        )
        res_values = get_supported_resolutions(0)
        self.controller.resolution_combo.configure(values=res_values)
        if res_values:
            self.controller.resolution_combo.set(res_values[0])
        self.controller.resolution_combo.grid(row=1, column=0, padx=5, pady=(0,5))

        # FPS label and dropdown
        ctk.CTkLabel(settings_frame, text="FPS:", font=ctk.CTkFont(family="Segoe UI")).grid(row=0, column=1, padx=5, pady=(5,2), sticky="w")
        self.controller.fps_combo = ctk.CTkComboBox(
            settings_frame,
            width=140,
            state="readonly",
            font=ctk.CTkFont(family="Segoe UI")
        )
        fps_vals = ["15", "30", "60"]
        self.controller.fps_combo.configure(values=fps_vals)
        self.controller.fps_combo.set(fps_vals[1])
        self.controller.fps_combo.grid(row=1, column=1, padx=5, pady=(0,5))

        # Codec label and dropdown
        ctk.CTkLabel(settings_frame, text="Codec:", font=ctk.CTkFont(family="Segoe UI")).grid(row=2, column=0, padx=5, pady=(5,2), sticky="w")
        self.controller.codec_combo = ctk.CTkComboBox(
            settings_frame,
            width=140,
            state="readonly",
            font=ctk.CTkFont(family="Segoe UI")
        )
        self.controller.codec_combo.configure(values=[])
        self.controller.codec_combo.set("<none>")
        self.controller.codec_combo.grid(row=3, column=0, padx=5, pady=(0,5))

        # Refresh Camera Settings Button
        refresh_settings_btn = ctk.CTkButton(
            settings_frame,
            text="Refresh Cam Settings",
            width=140,
            font=ctk.CTkFont(family="Segoe UI"),
            fg_color="red",
            hover_color="#b30000",
            command=self.refresh_codecs
        )
        refresh_settings_btn.grid(row=3, column=1, padx=5, pady=(5,10))

        # Hinweis-Label
        
        self.controller.mjpg_warning_label = ctk.CTkLabel(
            self.master,
            text="",
            text_color="orange",
            font=ctk.CTkFont(size=10, family="Segoe UI")
        )
        self.controller.mjpg_warning_label.pack(pady=(0,5))

        # Buttons zum Starten
        button_container = ctk.CTkFrame(self.master)
        button_container.pack(pady=15)
        row1 = ctk.CTkFrame(button_container, fg_color="transparent")
        row1.pack(pady=5)
        row2 = ctk.CTkFrame(button_container, fg_color="transparent")
        row2.pack(pady=10)
        btn_width = 140
        self.start_button = ctk.CTkButton(
            row1,
            text="Start Camera",
            width=btn_width,
            font=ctk.CTkFont(family="Segoe UI"),
            command=self.controller.start_camera
        )
        # Start-Button initial deaktivieren, bis ein gültiger Codec erkannt
        self.start_button.configure(state="disabled")
        self.start_button.pack(side="left", padx=5)
        ctk.CTkButton(
            row1,
            text="Fullscreen",
            width=btn_width,
            font=ctk.CTkFont(family="Segoe UI"),
            command=self.controller.toggle_fullscreen
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            row2,
            text="Screenshot",
            width=btn_width,
            font=ctk.CTkFont(family="Segoe UI"),
            command=self.controller.take_screenshot
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            row2,
            text="Set Save Folder",
            width=btn_width,
            font=ctk.CTkFont(family="Segoe UI"),
            command=self.controller.set_screenshot_path
        ).pack(side="left", padx=5)

        ctk.CTkLabel(
            self.master,
            text="Use mouse wheel in camera window to zoom",
            font=ctk.CTkFont(size=10, family="Segoe UI")
        ).pack(pady=(5,2))
        ctk.CTkLabel(
            self.master,
            text="by Jan Pultin",
            font=ctk.CTkFont(size=10, family="Segoe UI")
        ).pack(pady=(0,20))

    def refresh_cameras(self):
        # Ladefenster für Kameras
        loading = ctk.CTkToplevel(self.master)
        loading.title("🔄 Refresh Cameras")
        loading.geometry("300x100")
        center_window(loading, 300, 100)
        ctk.CTkLabel(loading, text="🔄 Refresh Cameras...", font=ctk.CTkFont(size=14)).pack(pady=10)
        progress = ctk.CTkProgressBar(loading, width=200)
        progress.pack(pady=5)
        progress.start()
        loading.transient(self.master)
        loading.grab_set()

        # Hintergrund-Thread zum Aktualisieren der Kameraliste
        def background():
            cams = get_available_cameras()
            def update_gui():
                self.controller.combo.configure(values=cams)
                if cams:
                    self.controller.combo.set(cams[0])
                loading.destroy()
            self.master.after(0, update_gui)

        threading.Thread(target=background, daemon=True).start()
        if self.controller.combo.cget("values"):
            self.controller.combo.set(self.controller.combo.cget("values")[0])

    def on_camera_selected(self):
        # automatisch bei Kamerawahl
        self.refresh_codecs()

    def refresh_codecs(self):
        # Ladefenster anzeigen
        loading = ctk.CTkToplevel(self.master)
        loading.title("🔍 Identify Codecs")
        loading.geometry("300x100")
        screen_w = self.master.winfo_screenwidth()
        screen_h = self.master.winfo_screenheight()
        x = (screen_w//2) - 150
        y = (screen_h//2) - 50
        loading.geometry(f"300x100+{x}+{y}")
        loading.resizable(False, False)
        ctk.CTkLabel(loading, text="🔍 Identify Codecs", font=ctk.CTkFont(size=14)).pack(pady=10)
        progress = ctk.CTkProgressBar(loading, width=200)
        progress.pack(pady=5)
        progress.start()
        loading.transient(self.master)
        loading.grab_set()

        import threading
        def background():
            # Kamera-Index auslesen
            cam_text = self.controller.combo.get()
            try:
                cam_index = int(cam_text.split()[-1])
            except Exception:
                codecs = []
                resolutions = []
                fps_list = []
            else:
                # Codecs ermitteln
                codecs = []
                for codec in ["MJPG","YUY2","NV12","RGB3"]:
                    cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
                    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*codec))
                    actual = int(cap.get(cv2.CAP_PROP_FOURCC))
                    try:
                        dec = actual.to_bytes(4,'little').decode(errors='replace')
                    except Exception:
                        dec = ''
                    cap.release()
                    if dec == codec:
                        codecs.append(codec)
                # Auflösungen ermitteln
                resolutions = get_supported_resolutions(cam_index)
                # FPS ermitteln
                fps_list = []
                cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
                for fps in [15, 30, 60]:
                    cap.set(cv2.CAP_PROP_FPS, fps)
                    actual_fps = cap.get(cv2.CAP_PROP_FPS)
                    if abs(actual_fps - fps) < 5:
                        fps_list.append(str(fps))
                cap.release()
            # GUI-Update im Hauptthread
            def update_gui():
                # Start-Button aktivieren/deaktivieren
                if codecs and codecs[0] != "<none supported>":
                    self.start_button.configure(state="normal")
                else:
                    self.start_button.configure(state="disabled")
                # Codec-Combo
                if codecs:
                    self.controller.codec_combo.configure(values=codecs)
                    self.controller.codec_combo.set(codecs[0])
                else:
                    self.controller.codec_combo.configure(values=["<none supported>"])
                    self.controller.codec_combo.set("<none supported>")
                # Auflösung-Combo
                if resolutions:
                    self.controller.resolution_combo.configure(values=resolutions)
                    self.controller.resolution_combo.set(resolutions[0])
                # FPS-Combo
                if fps_list:
                    self.controller.fps_combo.configure(values=fps_list)
                    self.controller.fps_combo.set(fps_list[0])
                loading.destroy()
            self.master.after(0, update_gui)
        threading.Thread(target=background, daemon=True).start()
