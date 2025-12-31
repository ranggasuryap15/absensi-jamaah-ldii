import flet as ft
import database as db
from datetime import datetime

def JadwalPage(page):
    # --- Input Form ---
    txt_kegiatan = ft.TextField(label="Nama Kegiatan (Cth: Pengajian Desa)")
    txt_tgl = ft.TextField(label="Tanggal (YYYY-MM-DD)", value=datetime.now().strftime("%Y-%m-%d"))
    txt_jam = ft.TextField(label="Jam (HH:MM)", value="19:30")
    
    def buat_jadwal(e):
        # Generate ID Unik sederhana (Timestamp)
        id_unik = "J" + datetime.now().strftime("%d%H%M")
        
        sukses, msg = db.tambah_jadwal(id_unik, txt_kegiatan.value, txt_tgl.value, txt_jam.value)
        
        page.snack_bar = ft.SnackBar(ft.Text(msg))
        page.snack_bar.open = True
        page.update()
        refresh_list()

    # --- List Jadwal ---
    list_view = ft.ListView(expand=True, spacing=10)

    def refresh_list():
        data = db.get_all_jadwal()
        list_view.controls.clear()
        for row in data:
            list_view.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.CALENDAR_MONTH),
                        ft.Column([
                            ft.Text(row[1], weight="bold"), # Nama
                            ft.Text(f"{row[2]} | {row[3]}", size=12) # Tgl Jam
                        ])
                    ]),
                    padding=10, bgcolor=ft.colors.BLUE_50, border_radius=10
                )
            )
        page.update()

    refresh_list()

    return ft.Column([
        ft.Text("Kelola Jadwal Pengajian", size=25, weight="bold"),
        ft.Container(
            content=ft.Column([
                txt_kegiatan, txt_tgl, txt_jam,
                ft.ElevatedButton("Buat Jadwal", on_click=buat_jadwal)
            ]),
            padding=20, border=ft.border.all(1, "grey"), border_radius=10
        ),
        ft.Divider(),
        ft.Text("Daftar Jadwal:"),
        ft.Container(content=list_view, height=300)
    ])