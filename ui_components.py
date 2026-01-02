import customtkinter as ctk
import tkinter as tk # Wajib untuk layar kamera stabil

class MainUI:
    def __init__(self, root):
        self.root = root
        
        # --- KONFIGURASI GRID UTAMA ---
        self.root.grid_columnconfigure(0, weight=0) # Sidebar
        self.root.grid_columnconfigure(1, weight=1) # Main Area
        self.root.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_main_area()

    def setup_sidebar(self):
        # Frame Sidebar
        self.sidebar = ctk.CTkFrame(self.root, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Header
        ctk.CTkLabel(self.sidebar, text="KONTROL PANEL", font=("Arial", 20, "bold"), text_color="#3B8ED0").pack(pady=(20, 10))

        # A. Input ID
        ctk.CTkLabel(self.sidebar, text="ID Jamaah:", anchor="w").pack(fill="x", padx=20, pady=(10,0))
        self.entry_id = ctk.CTkEntry(self.sidebar, placeholder_text="Scan / Ketik...", height=40, font=("Arial", 14))
        self.entry_id.pack(fill="x", padx=20, pady=(5, 10))

        # B. SEARCH 
        self.btn_cari = ctk.CTkButton(
            self.entry_id.master,  # <--- GANTI JADI INI (Otomatis ikut frame input ID)
            text="🔍 CARI NAMA (F2)",
            font=("Arial", 12, "bold"),
            fg_color="#E67E22",
            hover_color="#D35400",
            height=30,
            cursor="hand2"
        )
        self.btn_cari.pack(pady=(5, 15))

        # C. Status
        ctk.CTkLabel(self.sidebar, text="Status Kehadiran:", anchor="w").pack(fill="x", padx=20, pady=(5,0))
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

        # D. Keterangan
        ctk.CTkLabel(self.sidebar, text="Keterangan (Opsional):", anchor="w").pack(fill="x", padx=20, pady=(5,0))
        self.entry_ket = ctk.CTkEntry(self.sidebar, placeholder_text="...", height=40)
        self.entry_ket.pack(fill="x", padx=20, pady=(5, 20))

        # Tombol Simpan (Command nanti di-bind di main.py)
        self.btn_save = ctk.CTkButton(
            self.sidebar, 
            text="SIMPAN MANUAL", 
            fg_color="green", 
            hover_color="darkgreen",
            height=50,
            font=("Arial", 15, "bold")
        )
        self.btn_save.pack(fill="x", padx=20, pady=10)

        # Info Antrian
        self.lbl_queue = ctk.CTkLabel(self.sidebar, text="Antrian Upload: 0", text_color="gray")
        self.lbl_queue.pack(side="bottom", pady=20)

    def setup_main_area(self):
        self.main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.main_frame.grid_rowconfigure(0, weight=2) 
        self.main_frame.grid_rowconfigure(1, weight=0) 
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # --- AREA KAMERA (Menggunakan TKINTER LABEL AGAR STABIL) ---
        self.camera_box = ctk.CTkFrame(self.main_frame, fg_color="black")
        self.camera_box.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.camera_box.grid_propagate(False)

        # Widget Kamera Utama
        self.lbl_camera = tk.Label(self.camera_box, bg="black", text="Kamera Mati", fg="gray", font=("Arial", 12))
        self.lbl_camera.place(relx=0.5, rely=0.5, anchor="center")

        # Tombol Kamera
        self.btn_cam = ctk.CTkButton(
            self.main_frame, 
            text="NYALAKAN KAMERA", 
            height=40,
            font=("Arial", 14, "bold")
        )
        self.btn_cam.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # --- AREA LOG ---
        self.log_container = ctk.CTkFrame(self.main_frame)
        self.log_container.grid(row=2, column=0, sticky="nsew")
        
        header_log = ctk.CTkFrame(self.log_container, height=30, corner_radius=0, fg_color="#2b2b2b")
        header_log.pack(fill="x")
        ctk.CTkLabel(header_log, text="  RIWAYAT AKTIVITAS SYSTEM (LIVE)", font=("Consolas", 12, "bold"), text_color="#00ff00").pack(side="left")

        self.log_box = ctk.CTkTextbox(self.log_container, font=("Consolas", 14), activate_scrollbars=True, fg_color="#1a1a1a", text_color="#e0e0e0")
        self.log_box.pack(fill="both", expand=True, padx=2, pady=2)