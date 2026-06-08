"""
PATCH 01_data_generator.py
===========================
Ganti bagian berikut di dalam class PiiDataGenerator:

1. TAMBAHKAN import di bagian atas file (setelah baris from tqdm import tqdm):
   from nik_utils import generate_nik as _generate_nik_valid

2. GANTI metode generate_nik() dengan versi baru di bawah.

3. OPSIONAL: Update generate_phone() — sudah cukup bagus,
   hanya perlu perbaikan minor pada edge case.
"""

# ================================================================
# PATCH 1: Tambahkan import ini di atas file, setelah baris:
# from tqdm import tqdm
# ================================================================

# from nik_utils import generate_nik as _generate_nik_valid

# ================================================================
# PATCH 2: Ganti metode generate_nik() dengan ini:
# ================================================================

def generate_nik(self):
    """
    Generate NIK 16 digit VALID sesuai kaidah Dukcapil Indonesia.
    
    Perbaikan dari versi sebelumnya:
    ✓ Kode provinsi dari 34 kode valid (bukan randint 11-94)
    ✓ Tanggal 1-31 sesuai kapasitas bulan (bukan dibatasi 28)
    ✓ Validasi bulan vs tanggal termasuk tahun kabisat
    ✓ Tahun lahir 1940-2006 (generasi realistis, bukan hanya 1950-1999)
    ✓ Distribusi jenis kelamin 50:50
    
    Menggunakan shared module nik_utils.py sebagai sumber
    kebenaran tunggal (single source of truth) untuk struktur NIK.
    """
    return _generate_nik_valid()     # pakai nik_utils yang sudah divalidasi


# ================================================================
# PATCH 3: Perbaiki generate_phone() — edge case suffix terlalu panjang
# ================================================================

def generate_phone(self):
    """
    Generate nomor HP Indonesia valid.
    
    Aturan baku SDPPI:
    - Format lokal : 10-13 digit total (termasuk 0 di depan)
    - Format +62   : +62 diikuti 9-12 digit (mengganti 0 di depan)
    - Prefix       : hanya dari daftar operator resmi
    
    Perbaikan dari versi sebelumnya:
    ✓ Suffix length tidak bisa negatif atau 0
    ✓ Batas atas suffix dibatasi agar total tidak melebihi 13 digit
    """
    prefix = random.choice(self.phone_prefixes)   # 4 digit, misal "0812"
    
    # Target total: 10-13 digit
    # Prefix = 4 digit, jadi suffix = 6-9 digit
    suffix_length = random.randint(6, 9)
    suffix = ''.join([str(random.randint(0, 9)) for _ in range(suffix_length)])
    
    if random.random() < 0.3:
        # Format internasional: +62 menggantikan 0 di depan
        # "0812" → "+62812"
        return f"+62{prefix[1:]}{suffix}"
    
    # Format lokal: 08xxxxxxxxx
    return f"{prefix}{suffix}"


# ================================================================
# TIDAK PERLU UBAH: Bagian lain generator sudah bagus
# ================================================================
# - generate_pii_set()        ✓
# - generate_json_payload()   ✓ (4 template variasi)
# - generate_formdata_payload() ✓ (6 template variasi)
# - generate_narrative_payload() ✓ (7 template)
# - generate_negative_sample() ✓
# - generate_dataset()        ✓ (distribusi 40/40/15/5)
