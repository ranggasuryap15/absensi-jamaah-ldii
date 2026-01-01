import customtkinter as ctk

def create_header(parent):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    lbl_title = ctk.CTkLabel(frame, text="ABSENSI JAMAAH", font=ctk.CTkFont(size=24, weight="bold"), text_color="#ffffff")
    lbl_title.pack(pady=(20, 5))
    lbl_subtitle = ctk.CTkLabel(frame, text="Scan QR / Barcode Mode", font=ctk.CTkFont(size=12), text_color="gray")
    lbl_subtitle.pack(pady=(0, 20))
    return frame

def create_input_group(parent, label_text, placeholder, on_enter_callback=None):
    lbl = ctk.CTkLabel(parent, text=label_text, anchor="w")
    lbl.pack(padx=20, pady=(10, 0), fill="x")
    entry = ctk.CTkEntry(parent, placeholder_text=placeholder)
    entry.pack(padx=20, pady=5, fill="x")
    if on_enter_callback:
        entry.bind("<Return>", on_enter_callback)
    return entry

def create_dropdown_status(parent):
    lbl = ctk.CTkLabel(parent, text="Status Kehadiran:", anchor="w")
    lbl.pack(padx=20, pady=(10, 0), fill="x")
    dropdown = ctk.CTkOptionMenu(parent, values=["Hadir", "Izin", "Sakit", "Alfa"], fg_color="#1f6aa5", button_color="#144870")
    dropdown.pack(padx=20, pady=5, fill="x")
    return dropdown

def create_btn_simpan(parent, command):
    btn = ctk.CTkButton(parent, text="Simpan Manual", command=command, fg_color="green", hover_color="#006400")
    btn.pack(padx=20, pady=20, fill="x")
    return btn

def create_log_box(parent):
    log_box = ctk.CTkTextbox(parent, height=150)
    log_box.pack(padx=20, pady=(10, 20), fill="both", expand=True)
    return log_box

def create_camera_preview(parent):
    """
    Area Kamera.
    Kita set ukuran 0,0 agar dia mengikuti ukuran container induknya (responsive).
    """
    label = ctk.CTkLabel(
        parent, 
        text="Kamera Mati", 
        font=ctk.CTkFont(size=20),
        fg_color="black", 
        corner_radius=10,
        width=0, # Responsive
        height=0 # Responsive
    )
    # Gunakan sticky nsew di main.py nanti, disini pack expand true
    label.pack(expand=True, fill="both", padx=10, pady=10)
    return label

def create_btn_toggle_cam(parent, command):
    btn = ctk.CTkButton(parent, text="Nyalakan Kamera", command=command, height=50, font=ctk.CTkFont(size=16, weight="bold"), fg_color="#1f6aa5")
    
    return btn