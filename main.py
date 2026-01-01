import customtkinter as ctk
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

        # --- SETUP WINDOW ---
        self.title("Sistem Absensi Jamaah LDII - TURBO SCANNER")
        self.geometry("1100x700") 
        
        # GRID LAYOUT UTAMA
        # Kolom 0: Sidebar Input (Lebar tetap/kecil)
        # Kolom 1: Area Utama (Camera & Log Besar)
        self.grid_columnconfigure(0, weight=0) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=1)

        # =================================================
        # 1. SIDEBAR KIRI (FOKUS INPUT MANUAL)
        # =================================================
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False) # Paksa lebar sidebar tetap 300px

        # Header Simple
        ctk.CTkLabel(self.sidebar, text="KONTROL PANEL", font=("Arial", 20, "bold"), text_color="#3B8ED0").pack(pady=(20, 10))

        # --- INPUT ID ---
        ctk.CTkLabel(self.sidebar, text="ID Jamaah:", anchor="w").pack(fill="x", padx=20, pady=(10,0))
        self.entry_id = ctk.CTkEntry(self.sidebar, placeholder_text="Scan / Ketik...", height=40, font=("Arial", 14))
        self.entry_id.pack(fill="x", padx=20, pady=(5, 10))
        self.entry_id.bind("<Return>", self.on_enter_pressed)

        # --- STATUS KEHADIRAN (SOLUSI DROPDOWN) ---
        # Menggunakan Segmented Button agar lebih modern & cepat
        ctk.CTkLabel(self.sidebar, text="Status Kehadiran:", anchor="w").pack(fill="x", padx=20, pady=(10,0))
        self.status_var = ctk.StringVar(value="Hadir")
        self.seg_status = ctk.CTkSegmentedButton(
            self.sidebar, 
            values=["Hadir", "Izin", "Sakit", "Alfa"],
            variable=self.status_var,
            height=40,
            font=("Arial", 13, "bold"),
            selected_color="#1f6aa5",
            selected_hover_color="#144870"
        )
        self.seg_status.pack(fill="x", padx=20, pady=(5, 10))

        # --- KETERANGAN ---
        ctk.CTkLabel(self.sidebar, text="Keterangan (Opsional):", anchor="w").pack(fill="x", padx=20, pady=(10,0))
        self.entry_ket = ctk.CTkEntry(self.sidebar, placeholder_text="...", height=40)
        self.entry_ket.pack(fill="x", padx=20, pady=(5, 20))

        # --- TOMBOL SIMPAN ---
        self.btn_save = ctk.CTkButton(
            self.sidebar, 
            text="SIMPAN MANUAL", 
            fg_color="green", 
            hover_color="darkgreen",
            height=50,
            font=("Arial", 15, "bold"),
            command=self.simpan_data
        )
        self.btn_save.pack(fill="x", padx=20, pady=10)

        # Info Antrian
        self.lbl_queue = ctk.CTkLabel(self.sidebar, text="Antrian Upload: 0", text_color="gray")
        self.lbl_queue.pack(side="bottom", pady=20)

        # =================================================
        # 2. MAIN AREA (KAMERA & CONSOLE LOG)
        # =================================================
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Bagi Main Frame jadi 2 baris:
        # Row 0: Kamera (Weight 2 - Dominan)
        # Row 1: Tombol Kamera (Kecil)
        # Row 2: Console Log (Weight 1 - Cukup Besar)
        self.main_frame.grid_rowconfigure(0, weight=2) 
        self.main_frame.grid_rowconfigure(1, weight=0) 
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # --- A. AREA KAMERA ---
        self.camera_box = ctk.CTkFrame(self.main_frame, fg_color="black") # Bingkai hitam
        self.camera_box.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        self.lbl_camera = ctk.CTkLabel(self.camera_box, text="Kamera Mati", text_color="gray")
        self.lbl_camera.place(relx=0.5, rely=0.5, anchor="center") # Tengah presisi

        # --- B. TOMBOL KAMERA ---
        self.btn_cam = ctk.CTkButton(
            self.main_frame, 
            text="NYALAKAN KAMERA", 
            height=40,
            font=("Arial", 14, "bold"),
            command=self.toggle_camera
        )
        self.btn_cam.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # --- C. CONSOLE LOG (Solusi Log Kelihatan) ---
        # Frame khusus log dengan judul
        self.log_container = ctk.CTkFrame(self.main_frame)
        self.log_container.grid(row=2, column=0, sticky="nsew")
        
        # Judul Log
        header_log = ctk.CTkFrame(self.log_container, height=30, corner_radius=0, fg_color="#2b2b2b")
        header_log.pack(fill="x")
        ctk.CTkLabel(header_log, text="  RIWAYAT AKTIVITAS SYSTEM (LIVE)", font=("Consolas", 12, "bold"), text_color="#00ff00").pack(side="left")

        # Textbox Log Besar
        self.log_box = ctk.CTkTextbox(
            self.log_container, 
            font=("Consolas", 14), # Font Monospace Besar
            activate_scrollbars=True,
            fg_color="#1a1a1a", # Hitam terminal
            text_color="#e0e0e0"
        )
        self.log_box.pack(fill="both", expand=True, padx=2, pady=2)

        # --- SYSTEM VARIABLES ---
        self.cap = None
        self.is_camera_on = False
        self.last_scan_time = 0
        self.upload_queue = queue.Queue()
        self.local_cache = {}

        # Start Threads
        self.log("System initialized...")
        threading.Thread(target=self.load_cache_awal, daemon=True).start()
        threading.Thread(target=self.worker_uploader, daemon=True).start()

    # ==========================
    # LOGIC (Sama seperti sebelumnya)
    # ==========================
    def log(self, pesan, tipe="info"):
        waktu = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Simbol untuk mempercantik
        simbol = "[INFO]"
        if tipe == "success": simbol = "[OK  ]"
        if tipe == "error":   simbol = "[FAIL]"
        if tipe == "scan":    simbol = "[SCAN]"

        teks_lengkap = f"{waktu} {simbol} : {pesan}\n"
        
        self.log_box.insert("0.0", teks_lengkap)
        
        # Warnai teks tertentu (Opsional, fitur advanced)
        # Sederhananya kita biarkan putih/abu dulu biar performa cepat

    def toggle_camera(self):
        if not self.is_camera_on:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened(): self.cap = cv2.VideoCapture(0)
            self.is_camera_on = True
            self.btn_cam.configure(text="MATIKAN KAMERA", fg_color="red", hover_color="#8B0000")
            self.log("Kamera diaktifkan.", "info")
            self.update_frame()
        else:
            self.is_camera_on = False
            if self.cap: self.cap.release()
            self.lbl_camera.configure(image=None, text="Kamera Mati")
            self.btn_cam.configure(text="NYALAKAN KAMERA", fg_color="#1f6aa5", hover_color="#144870")
            self.log("Kamera dimatikan.", "info")

    def update_frame(self):
        if not self.is_camera_on: return
        ret, frame = self.cap.read()
        if ret:
            # Resize agar tidak melar, tapi agak besar karena area kamera luas
            # Kita sesuaikan tinggi 400-500px
            h, w, _ = frame.shape
            ratio = 480 / h 
            new_w = int(w * ratio)
            frame_resized = cv2.resize(frame, (new_w, 480))

            # Scan Logic
            decoded_objects = decode(frame_resized)
            for obj in decoded_objects:
                barcode_data = obj.data.decode("utf-8")
                current_time = time.time()
                if current_time - self.last_scan_time > 2.5:
                    self.last_scan_time = current_time
                    self.entry_id.delete(0, "end")
                    self.entry_id.insert(0, barcode_data)
                    self.log(f"Barcode terdeteksi: {barcode_data}", "scan")
                    self.simpan_data()

                # Gambar Kotak
                pts = obj.polygon
                if len(pts) == 4:
                    pts = [(p.x, p.y) for p in pts]
                    for i in range(4):
                        cv2.line(frame_resized, pts[i], pts[(i+1)%4], (0, 255, 0), 3)

            # Render
            img_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_tk = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(new_w, 480))
            
            self.lbl_camera.configure(image=img_tk, text="")
            self.after(10, self.update_frame)

    def load_cache_awal(self):
        try:
            self.local_cache = db.get_all_jamaah_dict()
            self.log(f"Cache dimuat: {len(self.local_cache)} data jamaah.", "success")
        except:
            self.log("Gagal memuat cache database.", "error")

    def worker_uploader(self):
        while True:
            tugas = self.upload_queue.get()
            if tugas:
                uid, status, ket, _ = tugas
                try:
                    db.input_absensi(uid, status, ket)
                except:
                    self.log(f"Gagal upload ID: {uid}", "error")
                finally:
                    self.upload_queue.task_done()
                    self.lbl_queue.configure(text=f"Antrian Upload: {self.upload_queue.qsize()}")

    def on_enter_pressed(self, event):
        self.simpan_data()

    def simpan_data(self):
        uid = self.entry_id.get()
        status = self.seg_status.get() # Ambil dari Segmented Button
        ket = self.entry_ket.get()

        if not uid: return

        nama = self.local_cache.get(str(uid), f"Unknown-{uid}")
        self.log(f"Input Data: {nama} | Status: {status}", "success")
        
        threading.Thread(target=lambda: winsound.Beep(2500, 200) if hasattr(winsound, 'Beep') else None, daemon=True).start()

        self.entry_id.delete(0, "end")
        self.entry_ket.delete(0, "end")
        self.upload_queue.put((uid, status, ket, time.time()))
        self.lbl_queue.configure(text=f"Antrian Upload: {self.upload_queue.qsize()}")

if __name__ == "__main__":
    app = AbsensiApp()
    app.mainloop()