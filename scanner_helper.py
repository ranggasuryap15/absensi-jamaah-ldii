import cv2
from pyzbar.pyzbar import decode
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import io

# Variabel Global untuk menyimpan frame terakhir & hasil scan
output_frame = None
found_qr_code = None
lock = threading.Lock()

class VideoStreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global output_frame, lock
        if self.path == '/video_feed':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            while True:
                with lock:
                    if output_frame is None:
                        continue
                    # Encode gambar ke JPEG
                    flag, encodedImage = cv2.imencode(".jpg", output_frame)
                    if not flag:
                        continue
                
                # Kirim data gambar sebagai stream (MJPEG)
                try:
                    self.wfile.write(b'--frame\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.end_headers()
                    self.wfile.write(bytearray(encodedImage))
                    self.wfile.write(b'\r\n')
                except Exception as e:
                    break # Client (Flet) menutup koneksi/pindah halaman
        else:
            self.send_error(404)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    pass

class CameraServer:
    def __init__(self):
        super().__init__()
        self.cap = None
        self.is_camera_on = False
        self.last_scan_time = 0
        self.current_image = None  # <--- TAMBAHKAN INI (Tempat simpan gambar)

    def start_server(self):
        """Mulai Kamera & Server HTTP"""
        if self.is_running: return

        self.is_running = True
        global found_qr_code
        found_qr_code = None # Reset hasil scan

        # 1. Thread Kamera (Producer)
        self.camera_thread = threading.Thread(target=self.update_frame, daemon=True)
        self.camera_thread.start()

        # 2. Thread Server (Consumer)
        self.server_thread = threading.Thread(target=self.run_http_server, daemon=True)
        self.server_thread.start()

    def stop_server(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()

    def get_last_qr(self):
        global found_qr_code
        if found_qr_code:
            temp = found_qr_code
            found_qr_code = None # Reset biar gak kebaca double
            return temp
        return None

    def run_http_server(self):
        # Jalankan server di port 5000 (Localhost)
        try:
            self.httpd = ThreadedHTTPServer(('0.0.0.0', 5000), VideoStreamHandler)
            self.httpd.serve_forever()
        except Exception as e:
            print(f"Server error: {e}")

    def update_frame(self):
        global output_frame, lock, found_qr_code
        
        # Buka kamera (pake cv2.CAP_DSHOW buat Windows biar cepet)
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
        frame_skip = 0

        while self.is_running:
            ret, frame = self.cap.read()
            if not ret: continue

            # --- LOGIKA SCANNING ---
            # Kita scan tiap 3 frame sekali biar video tetep ngebut 60FPS
            # walaupun proses scanning agak berat.
            frame_skip += 1
            if frame_skip % 3 == 0:
                try:
                    decoded_objects = decode(frame)
                    for obj in decoded_objects:
                        code = obj.data.decode("utf-8")
                        found_qr_code = code # Simpan hasil scan
                        
                        # Gambar kotak hijau
                        points = obj.polygon
                        if len(points) == 4:
                            import numpy as np
                            pts = np.array(points, dtype=np.int32)
                            cv2.polylines(frame, [pts], True, (0, 255, 0), 3)
                except:
                    pass

            # Update frame global untuk diambil server streaming
            with lock:
                output_frame = frame.copy()
            
            time.sleep(0.01) # Jeda dikit biar CPU gak 100%