import cv2
import os
import time
import numpy as np
from threading import Thread
from tkinter import filedialog
from screeninfo import get_monitors


class CameraController:
    def __init__(self, master):
        self.master = master
        self.cap = None
        self.running = False
        self.fullscreen = False
        self.zoom = 1.0
        self.window_name = "Live Vorschau"
        self.last_frame = None
        self.screenshot_path = os.getcwd()

        # GUI-Elemente (werden später in gui.py befüllt)
        self.combo = None
        self.monitor_combo = None
        self.resolution_combo = None
        self.fps_combo = None

    def update_resolutions(self, event=None):
        from viewer.camera import get_supported_resolutions
        cam_index = int(self.combo.get().split()[-1])
        resolutions = get_supported_resolutions(cam_index)
        if resolutions:
            self.resolution_combo.configure(values=resolutions)
            self.resolution_combo.set(resolutions[0])

    def start_camera(self, event=None):
        if self.cap:
            self.running = False
            self.cap.release()

        cam_index = int(self.combo.get().split()[-1])
        self.cap = cv2.VideoCapture(cam_index)

        width, height = map(int, self.resolution_combo.get().split("x"))
        fps = int(self.fps_combo.get())
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)

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

    def close_all(self):
        self.running = False
        self.cleanup_cv()
        self.master.destroy()
