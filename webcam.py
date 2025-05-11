import cv2
import customtkinter as ctk
from tkinter import filedialog
from threading import Thread
from screeninfo import get_monitors
import time
import os
import numpy as np

class CameraViewer:
    def __init__(self, master):
        self.master = master
        self.master.title("Microscope Video Viewer 1.0 by Jan Pultin")
        self.cap = None
        self.running = False
        self.fullscreen = False
        self.window_name = "Live Vorschau"
        self.zoom = 1.0
        self.last_frame = None
        self.screenshot_path = os.getcwd()

        self.center_window(400, 370)
        self.master.resizable(False, False)

        self.title_label = ctk.CTkLabel(master, text="Microscope Video Viewer 1.0",
                                        font=ctk.CTkFont(size=17, weight="bold", family="Segoe UI"))
        self.title_label.pack(pady=(15, 5))

        self.combo_label = ctk.CTkLabel(master, text="Choose Camera:", font=ctk.CTkFont(family="Segoe UI"))
        self.combo_label.pack()
        self.combo = ctk.CTkComboBox(master, width=300, state="readonly", font=ctk.CTkFont(family="Segoe UI"))
        self.combo.pack(pady=5)
        self.combo.configure(values=self.detect_cameras())

        self.monitor_label = ctk.CTkLabel(master, text="Choose Monitor:", font=ctk.CTkFont(family="Segoe UI"))
        self.monitor_label.pack()
        self.monitor_combo = ctk.CTkComboBox(master, width=300, state="readonly", font=ctk.CTkFont(family="Segoe UI"))
        self.monitor_combo.pack(pady=5)
        self.monitor_combo.configure(values=[f"Monitor {i+1} ({m.width}x{m.height})"
                                             for i, m in enumerate(get_monitors())])
        self.monitor_combo.set(self.monitor_combo.cget("values")[0])

        button_container = ctk.CTkFrame(master)
        button_container.pack(pady=15)

        row1 = ctk.CTkFrame(button_container, fg_color="transparent")
        row1.pack(pady=5)
        row2 = ctk.CTkFrame(button_container, fg_color="transparent")
        row2.pack(pady=10)

        button_width = 140

        self.start_button = ctk.CTkButton(row1, text="Start Camera", width=button_width,
                                          font=ctk.CTkFont(family="Segoe UI"), command=self.start_camera)
        self.start_button.pack(side="left", padx=10)

        self.fullscreen_button = ctk.CTkButton(row1, text="Fullscreen", width=button_width,
                                               font=ctk.CTkFont(family="Segoe UI"), command=self.toggle_fullscreen)
        self.fullscreen_button.pack(side="left", padx=10)

        self.screenshot_button = ctk.CTkButton(row2, text="Screenshot", width=button_width,
                                               font=ctk.CTkFont(family="Segoe UI"), command=self.take_screenshot)
        self.screenshot_button.pack(side="left", padx=10)

        self.path_button = ctk.CTkButton(row2, text="Set Save Folder", width=button_width,
                                         font=ctk.CTkFont(family="Segoe UI"), command=self.set_screenshot_path)
        self.path_button.pack(side="left", padx=10)

        self.author_label = ctk.CTkLabel(master, text="Use mouse wheel in camera window to zoom",
                                        font=ctk.CTkFont(size=10, family="Segoe UI"))
        self.author_label.pack(pady=(5, 2))

        self.author_label = ctk.CTkLabel(master, text="by Jan Pultin", font=ctk.CTkFont(size=10, family="Segoe UI"))
        self.author_label.pack(pady=(0, 10))

        self.master.protocol("WM_DELETE_WINDOW", self.close_all)
        self.master.bind("<F11>", self.toggle_fullscreen)

    def detect_cameras(self, max_cams=5):
        found = []
        for i in range(max_cams):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    found.append(f"Kamera {i}")
                cap.release()
        return found

    def start_camera(self, event=None):
        if self.cap:
            self.running = False
            self.cap.release()
        cam_index = int(self.combo.get().split()[-1])
        self.cap = cv2.VideoCapture(cam_index)
        self.running = True
        Thread(target=self.show_video, daemon=True).start()

    def show_video(self):
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_NORMAL)
        cv2.setMouseCallback(self.window_name, self.cv_mouse_zoom)

        selected_text = self.monitor_combo.get()
        selected_index = self.monitor_combo.cget("values").index(selected_text)
        monitor = get_monitors()[selected_index]
        positioned = False
        wait_for_fullscreen = 0

        while self.running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break

            self.last_frame = frame.copy()

            if not positioned:
                cv2.resizeWindow(self.window_name, 1280, 720)
                cv2.moveWindow(self.window_name, monitor.x, monitor.y)
                positioned = True

            if self.fullscreen:
                if wait_for_fullscreen == 0:
                    cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                    wait_for_fullscreen = 10
                wait_for_fullscreen -= 1
                w, h = monitor.width, monitor.height
            else:
                cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
                wait_for_fullscreen = 0
                h = int(cv2.getWindowImageRect(self.window_name)[3])
                w = int(cv2.getWindowImageRect(self.window_name)[2])

            if w > 0 and h > 0:
                h_zoomed = int(frame.shape[0] / self.zoom)
                w_zoomed = int(frame.shape[1] / self.zoom)
                x1 = (frame.shape[1] - w_zoomed) // 2
                y1 = (frame.shape[0] - h_zoomed) // 2
                zoomed = frame[y1:y1+h_zoomed, x1:x1+w_zoomed]

                target_aspect = 16 / 9
                if w / h > target_aspect:
                    new_h = h
                    new_w = int(h * target_aspect)
                else:
                    new_w = w
                    new_h = int(w / target_aspect)

                frame_resized = cv2.resize(zoomed, (new_w, new_h), interpolation=cv2.INTER_AREA)
                canvas = np.zeros((h, w, 3), dtype=np.uint8)
                y_offset = (h - new_h) // 2
                x_offset = (w - new_w) // 2
                canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = frame_resized

                cv2.imshow(self.window_name, canvas)

            key = cv2.waitKey(10) & 0xFF
            if key == 27:
                self.running = False
                break

        self.cleanup_cv()

    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen

    def cv_mouse_zoom(self, event, x, y, flags, param):
        if event == cv2.EVENT_MOUSEWHEEL:
            if flags > 0:
                self.zoom = min(5.0, self.zoom + 0.1)
            else:
                self.zoom = max(1.0, self.zoom - 0.1)

    def take_screenshot(self):
        if self.last_frame is not None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.screenshot_path, f"screenshot_{timestamp}.png")
            cv2.imwrite(filename, self.last_frame)
            print(f"Screenshot saved as {filename}")

    def set_screenshot_path(self):
        path = filedialog.askdirectory(title="Select Folder to Save Screenshots")
        if path:
            self.screenshot_path = path
            print(f"Save path set to: {self.screenshot_path}")



    def cleanup_cv(self):
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

    def center_window(self, width, height):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.master.geometry(f"{width}x{height}+{x}+{y}")

    def close_all(self):
        self.running = False
        self.cleanup_cv()
        self.master.destroy()

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    root = ctk.CTk()
    viewer = CameraViewer(root)
    root.mainloop()
