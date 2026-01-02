import customtkinter as ctk
import tkinter as tk 
from PIL import Image, ImageTk 
import cv2
from pyzbar.pyzbar import decode
import threading
import time
import queue 
import winsound
import datetime
import database as db       
import ui_components as ui 

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AbsensiApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistem Absensi Jamaah LDII - AUTO SCHEDULE")
        self.geometry("1100x700") 

        # 1. LOAD TAMPILAN
        self.ui = ui.MainUI(self)

        # 2. SAMBUNGKAN LOGIC
        self.ui.btn_save.configure(command=self.simpan_data)
        self.ui.btn_cam.configure(command=self.toggle_camera)
        self.ui.entry_id.bind("<Return>", self.on_enter_pressed)

        # --- BAGIAN CONFIG KEGIATAN DIHAPUS TOTAL DISINI ---

        # --- SYSTEM VARIABLES ---
        self.cap = None
        self.is_camera_on = False
        self.last_scan_time = 0
        self.upload_queue = queue.Queue()
        self.local_cache = {} 
        self.history_absen_sesi = set() 

        # Start Threads
        self.log("System initialized...")
        threading.Thread(target=self.load_cache_awal, daemon=True).start()
        threading.Thread(target=self.worker_uploader, daemon=True).start()

    # ==========================
    # LOGIC UTAMA
    # ==========================
    def log(self, pesan, tipe="info"):
        waktu = datetime.datetime.now().strftime("%H:%M:%S")
        simbol = "[INFO]"
        if tipe == "success": simbol = "[OK  ]"
        if tipe == "error":   simbol = "[FAIL]"
        if tipe == "scan":    simbol = "[SCAN]"
        
        self.ui.log_box.insert("0.0", f"{waktu} {simbol} : {pesan}\n")

    def toggle_camera(self):
        if not self.is_camera_on:
            try:
                self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) 
                if not self.cap.isOpened(): self.cap = cv2.VideoCapture(0)
                
                if not self.cap.isOpened():
                    self.log("Gagal mendeteksi kamera!", "error")
                    return

                self.is_camera_on = True
                self.ui.btn_cam.configure(text="MATIKAN KAMERA", fg_color="red", hover_color="#8B0000")
                self.log("Kamera aktif...", "info")
                self.update_frame()
                
            except Exception as e:
                self.log(f"Error start kamera: {e}", "error")
        else:
            self.is_camera_on = False
            self.log("Mematikan kamera...", "info")
            self.after(100, self._release_camera_resource)

    def _release_camera_resource(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        try:
            self.ui.lbl_camera.configure(image='', text="Kamera Mati", bg="black")
            if hasattr(self.ui.lbl_camera, 'image'):
                del self.ui.lbl_camera.image 
        except Exception:
            pass

        self.ui.btn_cam.configure(text="NYALAKAN KAMERA", fg_color="#1f6aa5", hover_color="#144870")
        self.log("Kamera Nonaktif.", "info")

    def update_frame(self):
        if not self.is_camera_on or self.cap is None: return

        ret, frame = self.cap.read()
        if ret:
            h, w, _ = frame.shape
            ratio = 480 / h 
            new_w = int(w * ratio)
            frame_resized = cv2.resize(frame, (new_w, 480))

            decoded_objects = decode(frame_resized)
            for obj in decoded_objects:
                barcode_data = obj.data.decode("utf-8")
                current_time = time.time()
                
                if current_time - self.last_scan_time > 2.5:
                    self.last_scan_time = current_time
                    self.ui.entry_id.delete(0, "end")
                    self.ui.entry_id.insert(0, barcode_data)
                    self.log(f"Scan Barcode: {barcode_data}", "scan")
                    
                    if hasattr(winsound, 'Beep'):
                        threading.Thread(target=winsound.Beep, args=(1000, 100), daemon=True).start()
                    
                    self.simpan_data()

                pts = obj.polygon
                if len(pts) == 4:
                    pts = [(p.x, p.y) for p in pts]
                    for i in range(4):
                        cv2.line(frame_resized, pts[i], pts[(i+1)%4], (0, 255, 0), 3)

            try:
                img_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(img_rgb)
                img_tk = ImageTk.PhotoImage(image=img_pil)
                self.ui.lbl_camera.image = img_tk 
                self.ui.lbl_camera.configure(image=img_tk, text="")
            except Exception:
                pass 

        if self.is_camera_on:
            self.ui.lbl_camera.after(10, self.update_frame)

    def load_cache_awal(self):
        try:
            self.local_cache = db.get_all_jamaah_dict()
            self.log(f"Cache Jamaah: {len(self.local_cache)} data.", "success")
            db.update_cache_jadwal()
            self.log("Cache Jadwal Updated.", "success")
        except Exception as e:
            self.log(f"Gagal memuat cache: {e}", "error")

    def worker_uploader(self):
        while True:
            tugas = self.upload_queue.get()
            if tugas:
                uid, status, ket, kegiatan_fix, _ = tugas
                try:
                    sukses = db.input_absensi(uid, status, ket, kegiatan_override=kegiatan_fix)
                    if not sukses:
                        self.log(f"GAGAL/DUPLIKAT SERVER: {uid}", "error")
                        winsound.Beep(500, 500) 
                except Exception as e:
                    self.log(f"Error Upload: {e}", "error")
                finally:
                    self.upload_queue.task_done()
                    self.ui.lbl_queue.configure(text=f"Antrian Upload: {self.upload_queue.qsize()}")

    def on_enter_pressed(self, event):
        self.simpan_data()

    def simpan_data(self):
        uid = self.ui.entry_id.get().strip()
        status = self.ui.status_var.get()
        ket = self.ui.entry_ket.get()
        
        self.ui.entry_id.delete(0, "end")
        self.ui.entry_ket.delete(0, "end")

        if not uid: return

        if uid not in self.local_cache:
            self.log(f"ID {uid} TIDAK TERDAFTAR!", "error")
            winsound.Beep(500, 400) 
            return
        
        data_jamaah = self.local_cache[uid]
        nama = data_jamaah['nama']
        desa_user = data_jamaah.get('desa', '-')
        kelompok_user = data_jamaah.get('kelompok', '-')

        # --- LOGIC KEGIATAN FULL DI BACKEND ---
        kegiatan_saat_ini = db.cek_sesi_aktif(desa_user, kelompok_user)
        
        tgl_skrg = datetime.datetime.now().strftime("%Y-%m-%d")
        kunci_unik = f"{uid}-{tgl_skrg}-{kegiatan_saat_ini}"

        if kunci_unik in self.history_absen_sesi:
            self.log(f"TOLAK: {nama} sudah absen '{kegiatan_saat_ini}'.", "error")
            threading.Thread(target=lambda: winsound.Beep(400, 600) if hasattr(winsound, 'Beep') else None, daemon=True).start()
            return

        self.log(f"Hadir: {nama} | {kegiatan_saat_ini}", "success")
        threading.Thread(target=lambda: winsound.Beep(2500, 200) if hasattr(winsound, 'Beep') else None, daemon=True).start()

        self.history_absen_sesi.add(kunci_unik)
        self.upload_queue.put((uid, status, ket, kegiatan_saat_ini, time.time()))
        self.ui.lbl_queue.configure(text=f"Antrian Upload: {self.upload_queue.qsize()}")

if __name__ == "__main__":
    app = AbsensiApp()
    app.mainloop()