import customtkinter as ctk
import tkinter as tk

class MainUI:
    def __init__(self, root):
        self.root = root
        self.setup_ui()

    def setup_ui(self):
        # Konfigurasi Grid Utama (Kiri Kecil, Kanan Besar)
        self.root.grid_columnconfigure(0, weight=0) # Sidebar (Fixed width)
        self.root.grid_columnconfigure(1, weight=1) # Main Content (Flexible)
        self.root.grid_rowconfigure(0, weight=1)

        # ===================================================
        # 1. FRAME KIRI (SIDEBAR / KONTROL PANEL)
        # ===================================================
        self.frame_kiri = ctk.CTkFrame(self.root, width=300, corner_radius=0)
        self.frame_kiri.grid(row=0, column=0, sticky="nsew")
        
        # Judul Sidebar
        self.lbl_judul = ctk.CTkLabel(self.frame_kiri, text="KONTROL PANEL", font=("Arial", 20, "bold"), text_color="#3498db")
        self.lbl_judul.pack(pady=(30, 20))

        # Input ID Jamaah
        self.lbl_id = ctk.CTkLabel(self.frame_kiri, text="ID Jamaah:", font=("Arial", 12))
        self.lbl_id.pack(pady=(10, 0), padx=20, anchor="w")
        
        self.entry_id = ctk.CTkEntry(self.frame_kiri, placeholder_text="Scan / Ketik...", font=("Arial", 16), height=40)
        self.entry_id.pack(fill="x", padx=20, pady=(5, 15))

        # Tombol Cari Nama (F2)
        self.btn_cari = ctk.CTkButton(
            self.frame_kiri,
            text="🔍 CARI NAMA (F2)",
            font=("Arial", 12, "bold"),
            fg_color="#E67E22",
            hover_color="#D35400",
            height=30,
            cursor="hand2"
        )
        self.btn_cari.pack(fill="x", padx=20, pady=(0, 20))

        # Pilihan Status Kehadiran
        self.lbl_status = ctk.CTkLabel(self.frame_kiri, text="Status Kehadiran:", font=("Arial", 12))
        self.lbl_status.pack(pady=(10, 0), padx=20, anchor="w")
        
        self.status_var = ctk.StringVar(value="Hadir")
        self.seg_status = ctk.CTkSegmentedButton(self.frame_kiri, values=["Hadir", "Izin", "Sakit", "Alfa"], variable=self.status_var)
        self.seg_status.pack(fill="x", padx=20, pady=(5, 15))

        # Keterangan Opsional
        self.lbl_ket = ctk.CTkLabel(self.frame_kiri, text="Keterangan (Opsional):", font=("Arial", 12))
        self.lbl_ket.pack(pady=(10, 0), padx=20, anchor="w")
        
        self.entry_ket = ctk.CTkEntry(self.frame_kiri, placeholder_text="...", font=("Arial", 14))
        self.entry_ket.pack(fill="x", padx=20, pady=(5, 20))

        # Tombol Simpan Manual
        self.btn_save = ctk.CTkButton(
            self.frame_kiri, 
            text="SIMPAN MANUAL", 
            fg_color="#008000", 
            hover_color="#006400",
            height=40,
            font=("Arial", 14, "bold")
        )
        self.btn_save.pack(fill="x", padx=20, pady=(10, 10))

        # Antrian Upload Label
        self.lbl_queue = ctk.CTkLabel(self.frame_kiri, text="Antrian Upload: 0", text_color="gray")
        self.lbl_queue.pack(side="bottom", pady=20)

        # --- TOMBOL LOGOUT (Di Bawah) ---
        self.btn_logout = ctk.CTkButton(
            self.frame_kiri,
            text="🚪 KELUAR",
            fg_color="#c0392b",
            hover_color="#a93226",
            height=35,
            cursor="hand2",
            font=("Arial", 12, "bold")
        )
        # Pack di atas lbl_queue sedikit
        self.btn_logout.pack(side="bottom", fill="x", padx=20, pady=(0, 10))


        # ===================================================
        # 2. FRAME KANAN (KAMERA & LOG)
        # ===================================================
        self.frame_kanan = ctk.CTkFrame(self.root, fg_color="transparent")
        self.frame_kanan.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.frame_kanan.grid_rowconfigure(0, weight=1) # Kamera area expand
        self.frame_kanan.grid_rowconfigure(1, weight=0) # Tombol kamera
        self.frame_kanan.grid_rowconfigure(2, weight=1) # Log area expand
        self.frame_kanan.grid_columnconfigure(0, weight=1)

        # --- DISPLAY KAMERA ---
        self.frame_cam = ctk.CTkFrame(self.frame_kanan, fg_color="black")
        self.frame_cam.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        self.lbl_camera = ctk.CTkLabel(self.frame_cam, text="Kamera Mati", text_color="gray", font=("Arial", 16))
        self.lbl_camera.place(relx=0.5, rely=0.5, anchor="center")

        # Tombol Toggle Kamera
        self.btn_cam = ctk.CTkButton(
            self.frame_kanan, 
            text="NYALAKAN KAMERA", 
            height=40, 
            font=("Arial", 14, "bold")
        )
        self.btn_cam.grid(row=1, column=0, sticky="ew", pady=(0, 15))

        # --- LOG AKTIVITAS ---
        self.lbl_log_title = ctk.CTkLabel(self.frame_kanan, text="RIWAYAT AKTIVITAS SYSTEM (LIVE)", font=("Consolas", 12, "bold"), text_color="#00FF00", anchor="w")
        self.lbl_log_title.grid(row=2, column=0, sticky="w", pady=(0, 5))

        self.log_box = ctk.CTkTextbox(self.frame_kanan, font=("Consolas", 12))
        self.log_box.grid(row=3, column=0, sticky="nsew")