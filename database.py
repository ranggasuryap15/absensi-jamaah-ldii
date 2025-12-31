import gspread
from datetime import datetime
import sys
import traceback
from config import SPREADSHEET_ID

CREDENTIALS_FILE = "credentials.json"

def connect_db():
    try:
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        sh = gc.open_by_key(SPREADSHEET_ID)
        return sh
    except Exception as e:
        print(f"❌ Error Koneksi DB: {e}")
        return None

# ==========================================
# 1. HELPER (Pencari Data)
# ==========================================

def get_jamaah_by_id(id_jamaah):
    """Mencari detail jamaah berdasarkan ID untuk melengkapi data absen"""
    sh = connect_db()
    if not sh: return None
    
    try:
        wks = sh.worksheet("MASTER_JAMAAH")
        data = wks.get_all_records()
        
        # Cari jamaah yang ID-nya cocok (pastikan tipe data string biar aman)
        for j in data:
            if str(j.get('id_jamaah')) == str(id_jamaah):
                return j # Mengembalikan dictionary data jamaah lengkap
        return None
    except:
        return None

def cek_sesi_aktif(desa_user, kelompok_user):
    """
    Logika Cerdas: Mencari nama kegiatan berdasarkan WAKTU, DESA, dan KELOMPOK.
    """
    sh = connect_db()
    if not sh: return ""

    # 1. Tentukan Hari Ini (Indonesia)
    hari_inggris = datetime.now().strftime("%A")
    kamus_hari = {
        "Sunday": "Minggu", "Monday": "Senin", "Tuesday": "Selasa",
        "Wednesday": "Rabu", "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu"
    }
    hari_ini = kamus_hari.get(hari_inggris, "Minggu")
    jam_sekarang = datetime.now().strftime("%H:%M") # Format "20:30"

    try:
        wks = sh.worksheet("JADWAL")
        jadwal_all = wks.get_all_records()
        
        for j in jadwal_all:
            # A. Cek Hari
            if str(j.get('hari')).lower() != hari_ini.lower():
                continue # Skip kalau harinya beda
            
            # B. Cek Lingkup (Desa & Kelompok)
            # Logika: Jadwal cocok jika Desa sama DAN (Kelompok sama ATAU Jadwal itu untuk semua kelompok "-")
            jadwal_desa = str(j.get('desa'))
            jadwal_kelompok = str(j.get('kelompok'))
            
            if jadwal_desa.lower() == desa_user.lower():
                if jadwal_kelompok == "-" or jadwal_kelompok == "" or jadwal_kelompok == kelompok_user:
                    # C. Cek Waktu (Range Jam)
                    # "20:00" <= "20:15" <= "21:30"
                    jam_mulai = str(j.get('waktu_mulai'))
                    jam_selesai = str(j.get('waktu_selesai'))
                    
                    if jam_mulai <= jam_sekarang <= jam_selesai:
                        return j.get('jenis_kegiatan') # KETEMU! Kembalikan nama kegiatannya
        
        return "" # Tidak ada jadwal yang pas
        
    except Exception as e:
        print(f"Error cek jadwal: {e}")
        return ""

# ==========================================
# 2. CRUD UTAMA
# ==========================================

def get_all_jamaah():
    """Mengambil semua data untuk dropdown (Hanya Nama & ID)"""
    sh = connect_db()
    if not sh: return []
    try:
        wks = sh.worksheet("MASTER_JAMAAH")
        data = wks.get_all_records()
        # Filter yang statusnya Aktif saja
        return [d for d in data if str(d.get('status')).lower() == 'aktif']
    except:
        return []

def input_absensi(id_jamaah, status_kehadiran, keterangan_input=""):
    """
    Fungsi Simpan Absen yang sudah DIPERBAIKI KOLOMNYA.
    Kita cuma butuh ID, sistem yang akan melengkapi sisanya (Nama, Gender, Sesi, dll).
    """
    sh = connect_db()
    if not sh: return False
    
    try:
        # 1. Ambil Data Lengkap Jamaah dulu (biar kolom Desa/Kelompok keisi otomatis)
        info_jamaah = get_jamaah_by_id(id_jamaah)
        if not info_jamaah:
            print("❌ ID Jamaah tidak ditemukan di Master!")
            return False

        nama_asli = info_jamaah.get('nama_lengkap')
        gender = info_jamaah.get('jenis_kelamin')
        kelompok = info_jamaah.get('kelompok')
        desa = info_jamaah.get('desa', 'Tambun') # Default Tambun jika kosong
        
        # 2. Cek Sesi Otomatis (Smart Schedule)
        # Jika jam cocok, sesi terisi. Jika tidak, kosong string ""
        nama_sesi = cek_sesi_aktif(desa, kelompok)
        
        # Jika sesi kosong (tidak pas jam pengajian), user minta "tidak perlu" ditulis
        # Jadi biarkan string kosong ""
        
        # 3. Siapkan Data Row (URUTAN INI PENTING! SESUAIKAN DENGAN SHEET LOG_ABSENSI)
        # A:timestamp | B:tanggal | C:nama | D:JK | E:status | F:kelompok | G:desa | H:ket | I:sesi
        
        now = datetime.now()
        row = [
            now.strftime("%Y-%m-%d %H:%M:%S"), # A: timestamp
            now.strftime("%Y-%m-%d"),          # B: tanggal
            nama_asli,                          # C: nama_jamaah (BENAR)
            gender,                             # D: jenis_kelamin (BENAR)
            status_kehadiran,                   # E: status
            kelompok,                           # F: kelompok
            desa,                               # G: desa
            keterangan_input,                   # H: keterangan
            nama_sesi                           # I: sesi (Otomatis)
        ]
        
        wks = sh.worksheet("LOG_ABSENSI")
        wks.append_row(row)
        print(f"✅ Data tersimpan: {nama_asli} - {nama_sesi}")
        return True

    except Exception as e:
        print(f"❌ Gagal simpan absen: {e}")
        traceback.print_exc()
        return False