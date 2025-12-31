# ui_components.py
import flet as ft

def get_header():
    return ft.Container(
        content=ft.Column([
            ft.Text("Sistem Absensi LDII", size=28, weight="bold", color="blue"),
            ft.Text("Hybrid Scan: USB & Camera", size=14, color="grey"),
            ft.Divider()
        ])
    )

def get_input_usb(on_submit_func):
    return ft.TextField(
        label="Klik disini untuk Scan USB",
        autofocus=True,
        prefix_icon=ft.icons.KEYBOARD,
        on_submit=on_submit_func,
        text_size=16
    )

def get_dropdown_jadwal(data_jadwal, on_change_func):
    opsi = []
    for row in data_jadwal:
        # row[0]=ID, row[1]=Nama, row[2]=Tanggal
        label = f"{row[1]} ({row[2]})"
        opsi.append(ft.dropdown.Option(key=row[0], text=label))
    
    return ft.Dropdown(
        label="Pilih Jadwal Pengajian",
        options=opsi,
        on_change=on_change_func,
        width=400
    )

def get_status_box():
    status_txt = ft.Text("Siap Scan...", size=20, weight="bold")
    detail_txt = ft.Text("-", size=16)
    
    container = ft.Container(
        content=ft.Column([status_txt, detail_txt], horizontal_alignment="center"),
        padding=20,
        bgcolor=ft.colors.BLUE_50,
        border_radius=10,
        width=400,
        alignment=ft.alignment.center
    )
    return container, status_txt, detail_txt

def get_image_control():
    return ft.Image(
        src_base64="",
        width=640,
        height=480,
        fit=ft.ImageFit.CONTAIN,
        border_radius=10
    )