import cv2

def get_available_cameras(max_cams=5):
    found = []
    for i in range(max_cams):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                found.append(f"Kamera {i}")
            cap.release()
    return found

def get_supported_resolutions(cam_index):
    test_resolutions = [(3840, 2160), (2560, 1440), (1920, 1080), (1280, 720)]
    working = []
    cap = cv2.VideoCapture(cam_index)
    for w, h in test_resolutions:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        actual_w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        if abs(actual_w - w) < 20 and abs(actual_h - h) < 20:
            working.append(f"{w}x{h}")
    cap.release()
    return working