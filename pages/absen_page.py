import flet as ft
import database as db

def AbsenPage(page):
    # Setup Dropdown Jadwal
    jadwal_data = db.get_all_jadwal()
    pilihan_jadwal = [ft.dropdown.Option(row[0], f"{row[1]} ({row[2]})") for row in jadwal_data]
    
    dd_jadwal = ft.Dropdown(label="Pilih Jadwal", options=pilihan_jadwal)
    
    txt_input = ft.TextField(
        label="Klik disini & Scan Barcode", 
        autofocus=True, 
        prefix_icon=ft.icons.QR_CODE
    )
    
    lbl_status = ft.Text("Siap Scan...", size=20, weight="bold")

    def proses_absen(e):
        kode = txt_input.value
        id_jadwal = dd_jadwal.value
        
        if not id_jadwal:
            lbl_status.value = "PILIH JADWAL DULU!"
            lbl_status.color = "red"
            page.update()
            return

        lbl_status.value = "Mencari..."
        page.update()
        
        # Logic Absen
        # 1. Cari Jamaah (Manual loop karena function cari di db.py mengembalikan row object)
        # Agar simpel kita asumsikan pakai try-except di database.py nanti
        # Disini kita pakai logic simpel:
        
        try:
            ws_jamaah = db.ws_jamaah
            cell = ws_jamaah.find(kode)
            if cell:
                nama = ws_jamaah.cell(cell.row, 2).value # Ambil kolom Nama
                db.simpan_kehadiran(id_jadwal, kode, nama)
                
                lbl_status.value = f"Hadir: {nama}"
                lbl_status.color = "green"
            else:
                lbl_status.value = "Data Tidak Dikenal"
                lbl_status.color = "red"
        except Exception as ex:
            lbl_status.value = "Error Koneksi"

        txt_input.value = ""
        txt_input.focus()
        page.update()

    txt_input.on_submit = proses_absen

    return ft.Column([
        ft.Text("Menu Absensi", size=25, weight="bold"),
        dd_jadwal,
        ft.Divider(),
        txt_input,
        ft.Container(
            content=lbl_status,
            padding=20, bgcolor=ft.colors.GREEN_50, border_radius=10,
            alignment=ft.alignment.center
        )
    ])