import flet as ft
import database as db

def JamaahPage(page):
    # --- 1. SETUP TABEL ---
    tabel_data = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Kode")),
            ft.DataColumn(ft.Text("Nama")),
            ft.DataColumn(ft.Text("Kelompok")),
            ft.DataColumn(ft.Text("Generus")),
            ft.DataColumn(ft.Text("Aksi")),
        ],
        rows=[]
    )

    def refresh_data():
        """Mengambil data terbaru dari GSheet"""
        rows = db.get_all_jamaah()
        tabel_data.rows.clear()
        for row in rows:
            # Row[0]=Kode, [1]=Nama, [2]=Kelompok, [5]=Generus (sesuaikan index excel anda)
            kode = row[0]
            tabel_data.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(row[0])),
                    ft.DataCell(ft.Text(row[1])),
                    ft.DataCell(ft.Text(row[2])),
                    ft.DataCell(ft.Text(row[5] if len(row)>5 else "-")),
                    ft.DataCell(
                        ft.IconButton(
                            icon=ft.icons.DELETE, 
                            icon_color="red",
                            on_click=lambda e, k=kode: hapus_data(k)
                        )
                    ),
                ])
            )
        page.update()

    def hapus_data(kode):
        sukses, msg = db.hapus_jamaah(kode)
        if sukses:
            page.snack_bar = ft.SnackBar(ft.Text("Data Dihapus"))
            page.snack_bar.open = True
            refresh_data()
        
    # --- 2. SETUP FORM TAMBAH (DIALOG) ---
    input_kode = ft.TextField(label="Kode Unik (Barcode)")
    input_nama = ft.TextField(label="Nama Lengkap")
    input_kelompok = ft.TextField(label="Kelompok")
    input_desa = ft.TextField(label="Desa")
    input_generus = ft.Dropdown(
        label="Generus",
        options=[
            ft.dropdown.Option("Caberawit"),
            ft.dropdown.Option("Pra Remaja"),
            ft.dropdown.Option("Remaja"),
            ft.dropdown.Option("Usia Nikah"),
            ft.dropdown.Option("Dewasa"),
        ]
    )

    def simpan_data(e):
        sukses, msg = db.tambah_jamaah(
            input_kode.value, input_nama.value, 
            input_kelompok.value, input_desa.value, input_generus.value
        )
        dialog.open = False
        page.update()
        
        # Tampilkan Notifikasi
        page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor="green" if sukses else "red")
        page.snack_bar.open = True
        
        if sukses:
            # Kosongkan form
            input_kode.value = ""
            input_nama.value = ""
            refresh_data() # Refresh tabel

    dialog = ft.AlertDialog(
        title=ft.Text("Tambah Jamaah"),
        content=ft.Column([
            input_kode, input_nama, input_kelompok, input_desa, input_generus
        ], height=400, tight=True),
        actions=[
            ft.TextButton("Batal", on_click=lambda e: page.close_dialog()),
            ft.ElevatedButton("Simpan", on_click=simpan_data),
        ]
    )

    def buka_dialog(e):
        page.dialog = dialog
        dialog.open = True
        page.update()

    # Load data saat pertama buka
    refresh_data()

    # --- 3. LAYOUT HALAMAN ---
    return ft.Column([
        ft.Row([
            ft.Text("Master Data Jamaah", size=25, weight="bold"),
            ft.ElevatedButton("Tambah Baru", icon=ft.icons.ADD, on_click=buka_dialog)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(),
        ft.ListView(controls=[tabel_data], expand=True, height=500)
    ])