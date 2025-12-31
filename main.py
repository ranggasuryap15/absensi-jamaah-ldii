import flet as ft
import database as db
import scanner as sc # Import file helper tadi
import time
import threading

def main(page: ft.Page):
    # Setup Halaman
    page.title = "Absensi Jamaah (Scan Mode)"
    page.theme_mode = "dark"
    page.window_width = 500
    page.window_height = 800
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # --- SETUP KAMERA ---
    camera = sc.CameraScanner()
    
    # Komponen Gambar (Untuk menampilkan video kamera)
    # Komponen Gambar (Untuk menampilkan video kamera)
    img_feed = ft.Image(
        src="",        # <--- GANTI JADI INI
        width=300, 
        height=200, 
        fit="contain",
        visible=False 
    )

    # --- KOMPONEN INPUT ---
    # 1. Input ID (Bisa diketik manual, USB Scanner, atau Hasil Kamera)
    input_id = ft.TextField(
        label="Scan ID / Ketik ID Jamaah",
        text_align=ft.TextAlign.CENTER,
        width=300,
        border_radius=10,
        autofocus=True, # Biar pas buka langsung siap ketik (buat USB Scanner)
        hint_text="Menunggu Scan..."
    )

    # 2. Status Kehadiran
    input_status = ft.Dropdown(
        label="Status",
        width=300,
        options=[
            ft.dropdown.Option("Hadir"),
            ft.dropdown.Option("Izin"),
            ft.dropdown.Option("Sakit"),
        ],
        value="Hadir",
        border_radius=10
    )

    # 3. Keterangan
    input_ket = ft.TextField(label="Keterangan", width=300, border_radius=10)

    # --- LOGIKA PROSES ABSEN ---
    def proses_absen(id_jamaah):
        """Fungsi sakti untuk memproses ID yang masuk"""
        if not id_jamaah: return

        # Kunci input biar gak spam
        input_id.disabled = True
        page.update()

        # Kirim ke Database
        sukses = db.input_absensi(
            id_jamaah=id_jamaah, 
            status_kehadiran=input_status.value, 
            keterangan_input=input_ket.value
        )

        if sukses:
            # Cari nama jamaah buat notif (Opsional, ambil dari DB helper)
            data_user = db.get_jamaah_by_id(id_jamaah)
            nama_user = data_user['nama_lengkap'] if data_user else "ID Tidak Dikenal"
            
            page.snack_bar = ft.SnackBar(ft.Text(f"✅ Sukses: {nama_user}"), bgcolor="green")
            
            # Reset
            input_id.value = ""
            input_ket.value = ""
            # Bunyi beep (Opsional, visual aja)
            input_id.focus() # Balikin kursor biar siap scan lagi
        else:
            page.snack_bar = ft.SnackBar(ft.Text(f"❌ ID {id_jamaah} Gagal/Tidak Ditemukan!"), bgcolor="red")
        
        input_id.disabled = False
        page.snack_bar.open = True
        input_id.focus()
        page.update()

    # Event saat USB Scanner menekan ENTER
    def on_usb_submit(e):
        proses_absen(input_id.value)

    input_id.on_submit = on_usb_submit

    # --- LOGIKA KAMERA ---
    def loop_kamera():
        """Looping background untuk update gambar"""
        while camera.is_running:
            frame_base64, code = camera.get_frame()
            if frame_base64:
                img_feed.src_base64 = frame_base64
                img_feed.update()

            if code:
                # KALO KETEMU QR CODE
                print(f"QR Ditemukan: {code}")
                # Matikan kamera dulu biar gak scan berkali-kali
                toggle_kamera(None) 
                
                # Masukkan ke text field & proses
                input_id.value = code
                input_id.update()
                proses_absen(code)
                break
            
            time.sleep(0.03) # Biar gak makan CPU (30 FPS)

    def toggle_kamera(e):
        """Tombol ON/OFF Kamera"""
        if not camera.is_running:
            # Nyalakan
            camera.start()
            img_feed.visible = True
            btn_cam.text = "Matikan Kamera"
            btn_cam.icon = ft.Icons.VIDEOCAM_OFF
            btn_cam.bgcolor = ft.Colors.RED_400
            page.update()
            
            # Jalankan thread terpisah biar UI gak macet
            threading.Thread(target=loop_kamera, daemon=True).start()
        else:
            # Matikan
            camera.stop()
            img_feed.visible = False
            btn_cam.text = "Scan QR / Barcode"
            btn_cam.icon = ft.Icons.QR_CODE_SCANNER
            btn_cam.bgcolor = ft.Colors.BLUE_600
            page.update()

    # Tombol Kamera
    btn_cam = ft.FilledButton(
        "Scan QR / Barcode",
        icon=ft.Icons.QR_CODE_SCANNER,
        on_click=toggle_kamera,
        width=300
    )

    # Tombol Submit Manual
    btn_manual = ft.ElevatedButton(
        "Simpan Manual",
        on_click=lambda _: proses_absen(input_id.value),
        width=300
    )

    # SUSUN UI
    page.add(
        ft.Column(
            [
                ft.Text("Absensi Scanner", size=30, weight="bold"),
                ft.Divider(),
                img_feed, # Layar Kamera
                btn_cam,  # Tombol On/Off Kamera
                ft.Container(height=20),
                ft.Text("Atau Scan via USB / Ketik:", size=12),
                input_id, # Input Utama
                input_status,
                input_ket,
                ft.Container(height=10),
                btn_manual
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )

if __name__ == "__main__":
    ft.app(target=main)