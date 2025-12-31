import cv2
from pyzbar.pyzbar import decode
import base64

class CameraScanner:
    def __init__(self):
        self.cap = None
        self.is_running = False

    def start(self, camera_index=0):
        """Mulai kamera"""
        self.cap = cv2.VideoCapture(camera_index)
        self.is_running = True

    def stop(self):
        """Matikan kamera"""
        self.is_running = False
        if self.cap:
            self.cap.release()

    def get_frame(self):
        """Ambil 1 frame gambar + Cek Barcode"""
        if not self.cap or not self.is_running:
            return None, None

        ret, frame = self.cap.read()
        if not ret:
            return None, None

        code_detected = None

        # 1. Cek ada Barcode/QR gak di frame ini?
        decoded_objects = decode(frame)
        for obj in decoded_objects:
            code_detected = obj.data.decode("utf-8") # Dapat string ID (misal: "001")
            
            # Gambar kotak di sekitar barcode (Visual effect)
            points = obj.polygon
            if len(points) == 4:
                pts = [points[i] for i in range(4)]
                # Gambar garis hijau
                for i in range(4):
                    cv2.line(frame, pts[i], pts[(i+1)%4], (0, 255, 0), 3)

        # 2. Convert gambar ke Base64 biar bisa tampil di Flet
        _, buffer = cv2.imencode('.jpg', frame)
        img_base64 = base64.b64encode(buffer).decode('utf-8')

        return img_base64, code_detected