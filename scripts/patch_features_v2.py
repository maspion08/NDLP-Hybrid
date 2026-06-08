"""
PATCH 07_features_v2.py
========================
Ganti fungsi validate_nik_structure() dengan versi dari nik_utils.
Ini memastikan konsistensi antara:
  - NIK yang digenerate (01_data_generator.py)
  - Fitur yang diekstrak (07_features_v2.py)
  - Deteksi di deployment (ndlp_addon.py)

LANGKAH:
1. Tambahkan import nik_utils di atas file
2. Ganti fungsi validate_nik_structure() yang lama
3. Tambahkan fitur score NIK (opsional tapi disarankan)
"""

# ================================================================
# PATCH 1: Tambahkan import ini setelah baris:
# import re
# ================================================================

# from nik_utils import validate_nik_structure, nik_structure_score

# ================================================================
# PATCH 2: HAPUS atau GANTI fungsi validate_nik_structure() lama:
#
# YANG LAMA (di 07_features_v2.py sekarang):
#   def validate_nik_structure(token):
#       if not (len(token) == 16 and token.isdigit()):
#           return False, False, False
#       try:
#           provinsi = int(token[0:2])
#           tanggal = int(token[6:8])
#           bulan = int(token[8:10])
#           prov_valid = 11 <= provinsi <= 94          ← TERLALU LEBAR
#           tanggal_valid = (1 <= tanggal <= 31) or (41 <= tanggal <= 71)
#           bulan_valid = 1 <= bulan <= 12
#           return True, prov_valid, (tanggal_valid and bulan_valid)
#       except:
#           return False, False, False
#
# GANTI DENGAN: (import dari nik_utils, sudah include di PATCH 1)
# Tidak perlu definisikan ulang karena sudah di-import.
# ================================================================


# ================================================================
# PATCH 3: Tambahkan fitur skor NIK di token_to_features_v2()
#
# Cari bagian ini di 07_features_v2.py:
#
#   if features['regex.matches_nik_pattern']:
#       is_16d, prov_valid, date_valid = validate_nik_structure(word)
#       features['regex.nik_structure_complete'] = is_16d and prov_valid and date_valid
#       features['regex.nik_province_valid'] = prov_valid
#       features['regex.nik_date_valid'] = date_valid
#   else:
#       features['regex.nik_structure_complete'] = False
#       features['regex.nik_province_valid'] = False
#       features['regex.nik_date_valid'] = False
#
# GANTI DENGAN:
# ================================================================

# ---- MULAI COPY dari sini ----

def _patch_nik_features(features, word):
    """
    Patch untuk bagian fitur NIK di token_to_features_v2().
    Ganti blok if/else NIK structure yang lama dengan ini.
    
    Perubahan utama:
    1. Pakai validate_nik_structure dari nik_utils (konsisten)
    2. Tambah fitur skor kontinu: regex.nik_likelihood (0.0-1.0)
       → Fitur ini lebih informatif daripada 3 boolean terpisah
       → Model ML bisa belajar dari gradasi, bukan hanya True/False
    """
    if features['regex.matches_nik_pattern']:
        is_16d, prov_valid, date_valid = validate_nik_structure(word)
        
        # Fitur boolean yang sudah ada (pertahankan untuk compatibility)
        features['regex.nik_structure_complete'] = is_16d and prov_valid and date_valid
        features['regex.nik_province_valid'] = prov_valid
        features['regex.nik_date_valid'] = date_valid
        
        # FITUR BARU: Skor kontinu likelihood NIK (0.0-1.0)
        # 0.0 = bukan 16 digit
        # 0.33 = 16 digit tapi provinsi invalid (kemungkinan Order ID)
        # 0.67 = 16 digit + provinsi valid tapi tanggal/bulan invalid
        # 1.0 = 16 digit + provinsi valid + tanggal/bulan valid
        features['regex.nik_likelihood'] = nik_structure_score(word)
        
    else:
        features['regex.nik_structure_complete'] = False
        features['regex.nik_province_valid'] = False
        features['regex.nik_date_valid'] = False
        features['regex.nik_likelihood'] = 0.0
    
    return features

# ---- SELESAI COPY ----

# ================================================================
# RINGKASAN PERUBAHAN DI 07_features_v2.py
# ================================================================
#
# SEBELUM (2 masalah):
#   prov_valid = 11 <= provinsi <= 94   ← 84 kode, harusnya 34 kode
#   Tidak ada fitur kontinu
#
# SESUDAH (perbaikan):
#   prov_valid via VALID_PROVINCE_CODES  ← hanya 34 kode valid
#   Tambah regex.nik_likelihood          ← fitur kontinu 0.0-1.0
#
# CATATAN: Perubahan ini TIDAK membutuhkan retrain model jika
# Anda hanya mengganti definisi validate_nik_structure().
# Fitur boolean (nik_structure_complete, nik_province_valid,
# nik_date_valid) tetap ada sehingga model lama masih bekerja.
#
# JIKA ingin tambah fitur nik_likelihood (disarankan):
# → Butuh RETRAIN karena menambah dimensi fitur baru.
# → Tapi peningkatan accuracy di adversarial diperkirakan signifikan.
# ================================================================
