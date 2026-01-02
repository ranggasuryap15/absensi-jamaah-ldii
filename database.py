import gspread
from datetime import datetime
import time
import sys
import traceback

# --- IMPORT CONFIGURASI ---
try:
    from config import (
        SPREADSHEET_ID, 
        SHEET_JAMAAH, 
        SHEET_JADWAL, 
        SHEET_USERS, 
        SHEET_LOG
    )
except ImportError:
    print("❌ ERROR: File config.py tidak ditemukan atau variabel kurang lengkap!")
    sys.exit()

CREDENTIALS_FILE = "credentials.json"

# --- GLOBAL CACHE (Agar Scanner Cepat) ---
CACHE_JADWAL = []
LAST_JADWAL_UPDATE = 0

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
    sh = connect_db()
    if not sh: return None
    try:
        wks = sh.worksheet(SHEET_JAMAAH) # Pakai variable dari config
        data = wks.get_all_records()
        for j in data:
            if str(j.get('id_jamaah')) == str(id_jamaah):
                return j 
        return None
    except:
        return None

def update_cache_jadwal():
    """Download jadwal dari Sheet dan simpan di RAM komputer"""
    global CACHE_JADWAL, LAST_JADWAL_UPDATE
    sh = connect_db()
    if sh:
        try:
            wks = sh.worksheet(SHEET_JADWAL) # Pakai variable dari config
            CACHE_JADWAL = wks.get_all_records()
            LAST_JADWAL_UPDATE = time.time()
            print(f"✅ Jadwal diperbarui: {len(CACHE_JADWAL)} aturan.")
        except Exception as e:
            print(f"❌ Gagal update jadwal: {e}")

def cek_sesi_aktif(desa_user, kelompok_user):
    """
    Logika Cerdas: Mencari nama kegiatan berdasarkan WAKTU, DESA, dan KELOMPOK.
    Menggunakan CACHE agar scan instan (tidak loading internet).
    """
    global CACHE_JADWAL
    
    # Jika cache kosong atau sudah lebih dari 1 jam, update dulu
    if not CACHE_JADWAL or (time.time() - LAST_JADWAL_UPDATE > 3600):
        update_cache_jadwal()

    hari_inggris = datetime.now().strftime("%A")
    kamus_hari = {
        "Sunday": "Minggu", "Monday": "Senin", "Tuesday": "Selasa",
        "Wednesday": "Rabu", "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu"
    }
    hari_ini = kamus_hari.get(hari_inggris, "Minggu")
    jam_sekarang = datetime.now().strftime("%H:%M") 

    for j in CACHE_JADWAL:
        # A. Cek Hari
        if str(j.get('hari')).lower() != hari_ini.lower():
            continue 
        
        # B. Cek Lingkup (Desa & Kelompok)
        jadwal_desa = str(j.get('desa'))
        jadwal_kelompok = str(j.get('kelompok'))
        
        # Normalisasi string (hilangkan spasi, lowercase)
        if jadwal_desa.strip().lower() == str(desa_user).strip().lower():
            # Jika jadwal untuk semua kelompok ("-") ATAU kelompok cocok
            if jadwal_kelompok in ["-", ""] or jadwal_kelompok.strip() == str(kelompok_user).strip():
                
                # C. Cek Waktu
                jam_mulai = str(j.get('waktu_mulai'))
                jam_selesai = str(j.get('waktu_selesai'))
                
                if jam_mulai <= jam_sekarang <= jam_selesai:
                    return j.get('jenis_kegiatan') 

    return "Kegiatan Umum" # Default jika tidak ada jadwal yg pas

# ==========================================
# 2. CRUD UTAMA
# ==========================================

def get_all_jamaah_dict():
    """
    Mengambil data ID, Nama, DESA, dan KELOMPOK untuk Cache Lokal.
    """
    sh = connect_db()
    if not sh: return {}
    try:
        wks = sh.worksheet(SHEET_JAMAAH) # Pakai variable dari config
        data = wks.get_all_records()
        
        cache_data = {}
        for row in data:
            id_jam = str(row.get('id_jamaah'))
            # Simpan data lengkap, bukan cuma nama
            cache_data[id_jam] = {
                'nama': row.get('nama_lengkap'),
                'desa': row.get('desa', 'Tambun'),       # Default Tambun
                'kelompok': row.get('kelompok', 'TB4')   # Default TB4
            }
            
        print(f"✅ Cache Loaded: {len(cache_data)} Jamaah (Data Lengkap)")
        return cache_data
    except Exception as e:
        print(f"❌ Gagal Load Cache: {e}")
        return {}

def input_absensi(id_jamaah, status_kehadiran, keterangan_input="", kegiatan_override=None):
    sh = connect_db()
    if not sh: return False
    
    try:
        # Ambil info jamaah (bisa dari cache sebenarnya, tapi double check ke DB aman)
        info_jamaah = get_jamaah_by_id(id_jamaah)
        if not info_jamaah: return False

        nama_asli = info_jamaah.get('nama_lengkap')
        gender = info_jamaah.get('jenis_kelamin')
        kelompok = info_jamaah.get('kelompok')
        desa = info_jamaah.get('desa')
        
        # Gunakan kegiatan yang dikirim dari UI (hasil hitungan logic di main.py)
        nama_sesi = kegiatan_override if kegiatan_override else "Kegiatan Umum"
        
        # LOGIC ANTI DUPLIKAT (Cek Log Hari Ini)
        wks_log = sh.worksheet(SHEET_LOG) # Pakai variable dari config
        now = datetime.now()
        tgl_skrg = now.strftime("%Y-%m-%d")
        
        # Cek Cepat Duplikat
        records = wks_log.get_all_values()
        for row in records:
            # Col B=Tanggal, Col C=Nama, Col I=Sesi
            if len(row) > 8:
                if row[1] == tgl_skrg and row[2] == nama_asli and row[8] == nama_sesi:
                    print(f"⚠️ Duplikat di DB: {nama_asli} - {nama_sesi}")
                    return False

        # Simpan
        row_data = [
            now.strftime("%Y-%m-%d %H:%M:%S"),
            tgl_skrg,
            nama_asli,
            gender,
            status_kehadiran,
            kelompok,
            desa,
            keterangan_input,
            nama_sesi
        ]
        
        wks_log.append_row(row_data)
        print(f"✅ Tersimpan: {nama_asli} @ {nama_sesi}")
        return True

    except Exception as e:
        print(f"❌ Gagal simpan: {e}")
        return False

def cek_login(username, password):
    """
    Mengembalikan data user (Role & Scope) jika login sukses.
    Return None jika gagal.
    """
    sh = connect_db()
    if not sh: return None
    
    try:
        wks = sh.worksheet(SHEET_USERS) # Pakai variable dari config
        users = wks.get_all_records() 
        
        print(f"DEBUG: Mencoba login user: {username}...")

        for u in users:
            # Ambil data dari sheet (Pastikan judul kolom di sheet adalah 'username' atau 'Username')
            # Kita paksa jadi string dan huruf kecil biar pencarian tidak case-sensitive
            db_user = str(u.get('username') or u.get('Username')).strip().lower()
            db_pass = str(u.get('password') or u.get('Password')).strip()
            
            input_user = username.strip().lower()
            input_pass = password.strip()
            
            # Cek kecocokan
            if db_user == input_user and db_pass == input_pass:
                print("DEBUG: Login Sukses!")
                return {
                    "role": u.get('role') or u.get('Role'),
                    "scope": u.get('scope') or u.get('Scope'),
                    "username": db_user
                }
        
        print("DEBUG: Username/Password salah.")
        return None 
    except Exception as e:
        print(f"❌ Error Login: {e}")
        return None