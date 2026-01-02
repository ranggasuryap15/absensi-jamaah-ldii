import customtkinter as ctk
import tkinter as tk 
from PIL import Image, ImageTk 
import cv2
from pyzbar.pyzbar import decode, ZBarSymbol
import threading
import time
import queue 
import winsound
import datetime
import database as db       
import ui_components as ui 

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ==========================
# 1. CLASS POPUP PENCARIAN
# ==========================
class SearchPopup(ctk.CTkToplevel):
    def __init__(self, parent, data_jamaah, on_select_callback, user_session):
        super().__init__(parent)
        self.data_jamaah = data_jamaah 
        self.on_select = on_select_callback
        self.user_session = user_session 
        
        self.title("Cari Nama Jamaah")
        self.geometry("500x600")
        self.attributes("-topmost", True) 
        
        role_info = f"{user_session['role'].upper()} ({user_session['scope']})"
        self.lbl_title = ctk.CTkLabel(self, text=f"Pencarian Khusus: {role_info}", font=("Arial", 14, "bold"))
        self.lbl_title.pack(pady=10)

        self.entry_search = ctk.CTkEntry(self, font=("Arial", 14), placeholder_text="Ketik Nama...")
        self.entry_search.pack(fill="x", padx=20, pady=(0, 10))
        self.entry_search.bind("<KeyRelease>", self.filter_data) 
        self.entry_search.focus_set()

        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.list_buttons = []
        self.filter_data(None) 

    def filter_data(self, event):
        keyword = self.entry_search.get().lower()
        role_admin = str(self.user_session.get('role', '')).lower()
        scope_admin = str(self.user_session.get('scope', '')).strip().lower()

        for btn in self.list_buttons: btn.destroy()
        self.list_buttons.clear()

        count = 0
        for uid, info in self.data_jamaah.items():
            nama = info['nama']
            desa_jamaah = str(info.get('desa', '-')).strip().lower()
            kelompok_jamaah = str(info.get('kelompok', '-')).strip().lower()

            # Filter Hak Akses
            if "kelompok" in role_admin and kelompok_jamaah != scope_admin: continue 
            if "desa" in role_admin and desa_jamaah != scope_admin: continue

            if keyword in nama.lower():
                text_tampil = f"{nama} - {info.get('desa', '-')} ({info.get('kelompok', '-')})"
                btn = ctk.CTkButton(self.scroll_frame, text=text_tampil, anchor="w", fg_color="transparent", 
                                    text_color="white", border_width=1, border_color="#333",
                                    command=lambda u=uid: self.pilih_jamaah(u))
                btn.pack(fill="x", pady=2)
                self.list_buttons.append(btn)
                count += 1
                if count >= 50: break 

    def pilih_jamaah(self, uid):
        self.on_select(uid)
        self.destroy()

# ==========================
# 2. MAIN APP
# ==========================
class AbsensiApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistem Absensi Jamaah LDII - LOGIN")
        self.geometry("400x500") 

        # Session Variables
        self.user_session = None 
        
        # System Variables
        self.cap = None
        self.is_camera_on = False
        self.last_scan_time = 0
        self.upload_queue = queue.Queue()
        self.local_cache = {} 
        self.history_absen_sesi = set() 
        
        # --- TAMBAHAN BARU: Variabel untuk melacak jendela popup ---
        self.popup_window = None 
        # -----------------------------------------------------------

        # Start Threads
        threading.Thread(target=self.load_cache_awal, daemon=True).start()
        threading.Thread(target=self.worker_uploader, daemon=True).start()

        self.show_login_screen()

    # --- BAGIAN LOGIN ---
    def show_login_screen(self):
        # Bersihkan container jika ada sisa widget
        for widget in self.winfo_children():
            widget.destroy()

        self.login_frame = ctk.CTkFrame(self)
        self.login_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.login_frame, text="🔐 LOGIN ADMIN", font=("Arial", 24, "bold")).pack(pady=(40, 20))

        self.entry_email = ctk.CTkEntry(self.login_frame, placeholder_text="Email", width=300)
        self.entry_email.pack(pady=10)

        self.entry_pass = ctk.CTkEntry(self.login_frame, placeholder_text="Password", show="*", width=300)
        self.entry_pass.pack(pady=10)
        self.entry_pass.bind("<Return>", self.proses_login)

        self.btn_login = ctk.CTkButton(self.login_frame, text="MASUK", height=40, command=lambda: self.proses_login(None))
        self.btn_login.pack(pady=20)

        self.lbl_msg = ctk.CTkLabel(self.login_frame, text="", text_color="red")
        self.lbl_msg.pack()

    def proses_login(self, event):
        email = self.entry_email.get()
        pwd = self.entry_pass.get()
        
        # Safe Update UI
        try:
            self.lbl_msg.configure(text="Sedang memeriksa...", text_color="yellow")
            self.update()
        except: pass

        try:
            user_data = db.cek_login(email, pwd)
            if user_data:
                self.user_session = user_data
                self.title(f"Absensi - {user_data['role'].upper()} ({user_data['scope']})")
                
                # Hapus Login Screen & Load Main App
                self.login_frame.destroy()
                self.geometry("1100x700") 
                self.init_main_app()
            else:
                try: self.lbl_msg.configure(text="Email atau Password Salah!", text_color="red")
                except: pass
        except Exception as e:
            try: self.lbl_msg.configure(text=f"Error DB: {e}", text_color="red")
            except: pass

    # --- LOGIC LOGOUT (SAFE MODE) ---
    def proses_logout(self):
        print("Proses Logout dimulai...")
        # 1. Matikan Kamera jika nyala
        if self.is_camera_on:
            self.toggle_camera()
            time.sleep(0.5) # Beri jeda agar kamera release sempurna
        
        # 2. Reset Session
        self.user_session = None
        self.title("Sistem Absensi Jamaah LDII - LOGIN")

        # 3. Hapus UI Utama (Explicit Destroy)
        # Hapus frame login jika ada
        if hasattr(self, 'login_frame') and self.login_frame.winfo_exists():
            self.login_frame.destroy()
        
        # Hapus frame utama (UI) jika ada
        if hasattr(self, 'ui') and hasattr(self.ui, 'main_frame'):
             try: self.ui.main_frame.destroy() # Hapus container UI
             except: pass
             del self.ui # Hapus object UI dari memory

        # 4. Hapus sisa widget (Brute Force Cleanup)
        for widget in self.winfo_children():
            try: widget.destroy()
            except: pass

        # 5. Kembali ke Login
        self.geometry("400x500")
        self.show_login_screen()

    # --- APP UTAMA ---
    def init_main_app(self):
        self.ui = ui.MainUI(self)

        self.ui.btn_save.configure(command=self.simpan_data)
        self.ui.btn_cam.configure(command=self.toggle_camera)
        
        try:
            self.ui.btn_cari.configure(command=self.buka_popup_cari)
            self.bind("<F2>", lambda event: self.buka_popup_cari()) 
        except: pass
        
        # Tombol Logout
        try:
            self.ui.btn_logout.configure(command=self.proses_logout)
        except: pass

        self.ui.entry_id.bind("<Return>", self.on_enter_pressed)
        self.log(f"Login sukses: {self.user_session['email']}", "success")

    # --- UTILS (SAFE LOGGING ADDED) ---
    def log(self, pesan, tipe="info"):
        waktu = datetime.datetime.now().strftime("%H:%M:%S")
        simbol = "[INFO]"
        if tipe == "success": simbol = "[OK  ]"
        if tipe == "error":   simbol = "[FAIL]"
        if tipe == "scan":    simbol = "[SCAN]"
        
        # Print ke terminal selalu jalan (untuk debugging)
        print(f"{waktu} {simbol} : {pesan}")

        # Update ke UI HANYA JIKA UI MASIH ADA
        # (Mencegah crash saat Logout tapi thread masih jalan)
        if hasattr(self, 'ui') and hasattr(self.ui, 'log_box'):
            try:
                # Cek apakah widget log_box benar-benar exist di window
                if self.ui.log_box.winfo_exists():
                    self.ui.log_box.insert("0.0", f"{waktu} {simbol} : {pesan}\n")
            except: 
                pass 

    def buka_popup_cari(self):
        # 1. Cek apakah data jamaah sudah siap
        if not self.local_cache:
            self.log("Data Jamaah belum dimuat!", "error")
            return
        
        # 2. LOGIKA ANTI DUPLIKAT WINDOW
        # Cek apakah popup_window sudah ada isinya DAN jendelanya masih eksis (belum di-close 'X')
        if self.popup_window is not None and self.popup_window.winfo_exists():
            # Jika sudah ada, angkat ke depan (focus) saja, jangan bikin baru
            self.popup_window.lift()
            self.popup_window.focus()
            return

        # 3. Jika belum ada, buat baru dan simpan ke variabel self.popup_window
        self.popup_window = SearchPopup(self, self.local_cache, self.hasil_pencarian_dipilih, self.user_session)

    def hasil_pencarian_dipilih(self, uid_dipilih):
        self.ui.entry_id.delete(0, "end")
        self.ui.entry_id.insert(0, uid_dipilih)
        self.log(f"Manual Input: ID {uid_dipilih}", "info")
        self.simpan_data()

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
        desa_jamaah = data_jamaah.get('desa', '-')
        kelompok_jamaah = data_jamaah.get('kelompok', '-')

        role_user = str(self.user_session.get('role', '')).lower()
        scope_user = str(self.user_session.get('scope', '')).strip().lower()

        izin_ok = False
        if "pusat" in role_user or scope_user == "all": izin_ok = True
        elif "desa" in role_user and str(desa_jamaah).strip().lower() == scope_user: izin_ok = True
        elif "kelompok" in role_user and str(kelompok_jamaah).strip().lower() == scope_user: izin_ok = True

        if not izin_ok:
            self.log(f"DITOLAK: {nama} beda scope.", "error")
            threading.Thread(target=lambda: winsound.Beep(500, 1000) if hasattr(winsound, 'Beep') else None, daemon=True).start()
            return

        kegiatan_saat_ini = db.cek_sesi_aktif(desa_jamaah, kelompok_jamaah)
        tgl_skrg = datetime.datetime.now().strftime("%Y-%m-%d")
        kunci_unik = f"{uid}-{tgl_skrg}-{kegiatan_saat_ini}"

        if kunci_unik in self.history_absen_sesi:
            self.log(f"TOLAK: {nama} sudah absen.", "error")
            threading.Thread(target=lambda: winsound.Beep(400, 600) if hasattr(winsound, 'Beep') else None, daemon=True).start()
            return

        self.log(f"Hadir: {nama} | {kegiatan_saat_ini}", "success")
        threading.Thread(target=lambda: winsound.Beep(2500, 200) if hasattr(winsound, 'Beep') else None, daemon=True).start()
        self.history_absen_sesi.add(kunci_unik)
        self.upload_queue.put((uid, status, ket, kegiatan_saat_ini, time.time()))
        try: self.ui.lbl_queue.configure(text=f"Antrian Upload: {self.upload_queue.qsize()}")
        except: pass

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
        
        # Safe UI Update
        try:
            self.ui.lbl_camera.configure(image='', text="Kamera Mati", bg="black")
            if hasattr(self.ui.lbl_camera, 'image'): del self.ui.lbl_camera.image 
        except: pass
        
        try: self.ui.btn_cam.configure(text="NYALAKAN KAMERA", fg_color="#1f6aa5", hover_color="#144870")
        except: pass
        self.log("Kamera Nonaktif.", "info")

    def update_frame(self):
        if not self.is_camera_on or self.cap is None: return
        ret, frame = self.cap.read()
        if ret:
            h, w, _ = frame.shape
            ratio = 480 / h 
            new_w = int(w * ratio)
            frame_resized = cv2.resize(frame, (new_w, 480))
            decoded_objects = decode(frame_resized, symbols=[ZBarSymbol.QRCODE, ZBarSymbol.CODE128])
            
            for obj in decoded_objects:
                barcode_data = obj.data.decode("utf-8")
                current_time = time.time()
                if current_time - self.last_scan_time > 2.5:
                    self.last_scan_time = current_time
                    try:
                        self.ui.entry_id.delete(0, "end")
                        self.ui.entry_id.insert(0, barcode_data)
                    except: pass

                    self.log(f"Scan Barcode: {barcode_data}", "scan")
                    if hasattr(winsound, 'Beep'): threading.Thread(target=winsound.Beep, args=(1000, 100), daemon=True).start()
                    self.simpan_data()
                pts = obj.polygon
                if len(pts) == 4:
                    pts = [(p.x, p.y) for p in pts]
                    for i in range(4): cv2.line(frame_resized, pts[i], pts[(i+1)%4], (0, 255, 0), 3)
            try:
                img_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(img_rgb)
                img_tk = ImageTk.PhotoImage(image=img_pil)
                self.ui.lbl_camera.image = img_tk 
                self.ui.lbl_camera.configure(image=img_tk, text="")
            except: pass 
        if self.is_camera_on: self.ui.lbl_camera.after(10, self.update_frame)

    def load_cache_awal(self):
        try:
            self.local_cache = db.get_all_jamaah_dict()
            print(f"Cache Jamaah: {len(self.local_cache)} data.")
            db.update_cache_jadwal()
            print("Cache Jadwal Updated.")
        except Exception as e:
            print(f"Gagal memuat cache: {e}")

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
                    try: self.ui.lbl_queue.configure(text=f"Antrian Upload: {self.upload_queue.qsize()}")
                    except: pass

if __name__ == "__main__":
    app = AbsensiApp()
    app.mainloop()