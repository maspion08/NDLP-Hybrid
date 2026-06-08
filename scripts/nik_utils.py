"""
nik_utils.py - Shared NIK Utilities
Tugas Akhir: Arga Ariyuda Avian (2221101774)

SATU SUMBER KEBENARAN untuk struktur NIK Indonesia.
Digunakan oleh:
  - 01_data_generator.py  (generate NIK valid)
  - 07_features_v2.py     (validate NIK di feature extraction)
  - ndlp_addon.py         (validate NIK di deployment)

Referensi:
  - Permendagri No. 137 Tahun 2017 (Kode wilayah)
  - Peraturan Dukcapil (Format NIK)
  - Informasi resmi Disdukcapil: PP KK CC DD MM YY NNNN

Struktur NIK 16 digit:
  PP   = Kode Provinsi (2 digit, dari 34 kode valid)
  KK   = Kode Kabupaten/Kota (2 digit, 01-99)
  CC   = Kode Kecamatan (2 digit, 01-99)
  DD   = Tanggal lahir:
           Laki-laki  : 01-31 (tanggal asli)
           Perempuan  : 41-71 (tanggal + 40)
  MM   = Bulan lahir (01-12)
  YY   = Dua digit terakhir tahun lahir (00-99)
  NNNN = Nomor urut penerbitan Dukcapil (0001-9999)
"""

import random
import calendar

# ============================================================
# KODE PROVINSI VALID (34 Provinsi per Permendagri 137/2017)
# ============================================================
VALID_PROVINCE_CODES = {
    11: "Aceh",
    12: "Sumatera Utara",
    13: "Sumatera Barat",
    14: "Riau",
    15: "Jambi",
    16: "Sumatera Selatan",
    17: "Bengkulu",
    18: "Lampung",
    19: "Kepulauan Bangka Belitung",
    21: "Kepulauan Riau",
    31: "DKI Jakarta",
    32: "Jawa Barat",
    33: "Jawa Tengah",
    34: "DI Yogyakarta",
    35: "Jawa Timur",
    36: "Banten",
    51: "Bali",
    52: "Nusa Tenggara Barat",
    53: "Nusa Tenggara Timur",
    61: "Kalimantan Barat",
    62: "Kalimantan Tengah",
    63: "Kalimantan Selatan",
    64: "Kalimantan Timur",
    65: "Kalimantan Utara",
    71: "Sulawesi Utara",
    72: "Sulawesi Tengah",
    73: "Sulawesi Selatan",
    74: "Sulawesi Tenggara",
    75: "Gorontalo",
    76: "Sulawesi Barat",
    81: "Maluku",
    82: "Maluku Utara",
    91: "Papua",
    94: "Papua Barat",
}

VALID_PROVINCE_LIST = list(VALID_PROVINCE_CODES.keys())


def _max_day_in_month(month: int, year_2digit: int) -> int:
    """
    Mengembalikan jumlah hari maksimum dalam suatu bulan.
    Untuk tahun kabisat: asumsi rentang tahun 1940-2029.
    
    Args:
        month: 1-12
        year_2digit: 0-99 (YY dari NIK)
    
    Returns:
        Jumlah hari maksimum (28, 29, 30, atau 31)
    """
    # Konversi YY ke tahun 4-digit
    if year_2digit <= 29:           # 00-29 → 2000-2029
        year_4digit = 2000 + year_2digit
    else:                           # 30-99 → 1930-1999
        year_4digit = 1900 + year_2digit

    return calendar.monthrange(year_4digit, month)[1]


# ============================================================
# GENERATOR NIK VALID
# ============================================================

def generate_nik(rng=None) -> str:
    """
    Generate NIK 16 digit yang VALID secara struktural.
    
    Perbaikan dari versi Faker sederhana:
    1. Kode provinsi dari daftar 34 kode valid saja
    2. Tanggal sesuai kapasitas bulan (validasi kabisat)
    3. Tanggal 01-31 (tidak dibatasi 28)
    4. Tahun mencakup kelahiran 1940-2006 (usia realistis)
    5. Distribusi jenis kelamin 50:50
    
    Args:
        rng: random.Random instance untuk reproducibility
             Kalau None, pakai modul random global.
    
    Returns:
        String NIK 16 digit yang valid
    """
    r = rng if rng else random

    # PP: Kode provinsi dari 34 kode valid
    prov = r.choice(VALID_PROVINCE_LIST)

    # KK: Kode kabupaten/kota (01-99)
    kab = r.randint(1, 99)

    # CC: Kode kecamatan (01-99)
    kec = r.randint(1, 99)

    # YY: Dua digit terakhir tahun lahir
    # Rentang usia realistis: lahir 1940-2006 (usia 18-84 pada 2024)
    # YY = 40-99 → 1940-1999
    # YY = 00-06 → 2000-2006
    yy_options = list(range(40, 100)) + list(range(0, 7))
    yy = r.choice(yy_options)

    # MM: Bulan lahir (01-12)
    mm = r.randint(1, 12)

    # DD: Tanggal lahir dengan validasi per bulan
    max_day = _max_day_in_month(mm, yy)
    tanggal_asli = r.randint(1, max_day)

    # Jenis kelamin: 50% laki, 50% perempuan
    if r.random() < 0.5:
        # Perempuan: tanggal + 40
        dd = tanggal_asli + 40
    else:
        # Laki-laki: tanggal asli
        dd = tanggal_asli

    # NNNN: Nomor urut penerbitan (0001-9999)
    nnnn = r.randint(1, 9999)

    nik = f"{prov:02d}{kab:02d}{kec:02d}{dd:02d}{mm:02d}{yy:02d}{nnnn:04d}"

    # Sanity check panjang
    assert len(nik) == 16, f"NIK harus 16 digit, dapat {len(nik)}: {nik}"
    assert nik.isdigit(), f"NIK harus semua angka: {nik}"

    return nik


# ============================================================
# VALIDATOR NIK STRUKTURAL
# ============================================================

def validate_nik_structure(token: str) -> tuple:
    """
    Validasi apakah suatu string memenuhi kaidah struktural NIK Indonesia.
    
    Digunakan di:
    - 07_features_v2.py → sebagai FITUR (bukan hard filter!)
    - ndlp_addon.py     → untuk scoring likelihood
    
    Args:
        token: string yang akan divalidasi
    
    Returns:
        Tuple (is_16digit, prov_valid, date_valid) semua boolean.
        
    CATATAN PENTING:
        Fungsi ini mengembalikan 3 nilai terpisah agar model ML bisa
        memperlakukannya sebagai FITUR TERPISAH, bukan satu keputusan
        binary. Model yang memutuskan, bukan rule ini.
    """
    # Cek panjang & semua digit
    if not (len(token) == 16 and token.isdigit()):
        return False, False, False

    try:
        prov    = int(token[0:2])
        tanggal = int(token[6:8])
        bulan   = int(token[8:10])
        yy      = int(token[10:12])

        # Validasi provinsi: harus dari 34 kode valid
        prov_valid = prov in VALID_PROVINCE_CODES

        # Validasi bulan: 01-12
        if not (1 <= bulan <= 12):
            return True, prov_valid, False

        # Decode tanggal (perempuan: tanggal - 40)
        if tanggal > 40:
            tanggal_riil = tanggal - 40   # perempuan
        else:
            tanggal_riil = tanggal        # laki-laki

        # Validasi tanggal minimal
        if tanggal_riil < 1:
            return True, prov_valid, False

        # Validasi tanggal maksimal (sesuai bulan dan tahun kabisat)
        max_day = _max_day_in_month(bulan, yy)
        date_valid = (1 <= tanggal_riil <= max_day)

        return True, prov_valid, date_valid

    except (ValueError, IndexError):
        return False, False, False


def nik_structure_score(token: str) -> float:
    """
    Hitung skor 0.0-1.0 seberapa NIK-like suatu token.
    Digunakan sebagai FITUR KONTINU di feature extractor.
    
    Score:
        0.0  = bukan 16 digit sama sekali
        0.33 = 16 digit tapi provinsi invalid
        0.67 = 16 digit + provinsi valid tapi tanggal/bulan invalid
        1.0  = 16 digit + provinsi valid + tanggal/bulan valid
    """
    is_16d, prov_valid, date_valid = validate_nik_structure(token)

    if not is_16d:
        return 0.0
    if not prov_valid:
        return 0.33
    if not date_valid:
        return 0.67
    return 1.0


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("  NIK UTILS - SELF TEST")
    print("=" * 60)

    # Test 1: Generate 10 NIK dan validasi semuanya
    print("\n[TEST 1] Generate 10 NIK valid:")
    print("-" * 60)

    rng = random.Random(2026)  # seed tetap untuk reproducibility
    all_valid = True

    for i in range(10):
        nik = generate_nik(rng)
        is_16d, prov_valid, date_valid = validate_nik_structure(nik)
        score = nik_structure_score(nik)
        prov_code = int(nik[0:2])
        prov_name = VALID_PROVINCE_CODES.get(prov_code, "INVALID")
        status = "✅" if (is_16d and prov_valid and date_valid) else "❌"
        print(f"  {status} {nik}  |  {prov_name:<25}  |  score={score:.2f}")
        if not (is_16d and prov_valid and date_valid):
            all_valid = False

    print(f"\n  Hasil: {'SEMUA VALID ✓' if all_valid else 'ADA YANG INVALID ✗'}")

    # Test 2: Validasi kasus edge
    print("\n[TEST 2] Edge cases:")
    print("-" * 60)

    test_cases = [
        ("3201234567890123", "NIK laki-laki valid (Jawa Barat)"),
        ("3274635212890001", "NIK perempuan valid (tanggal+40=52)"),
        ("9876543210987654", "Order ID fake (prov 98 invalid)"),
        ("2001010102001234", "Kode prov 20 (TIDAK ADA)"),
        ("3201310102001234", "Tanggal 31 bulan Februari (invalid)"),
        ("3274021302001234", "Tanggal 02 Feb 2000 (tahun kabisat, valid)"),
        ("3274021302011234", "Tanggal 02 Feb 2001 (non-kabisat, valid)"),
        ("abcdefghijklmnop", "Bukan angka"),
        ("32012345678901",   "Hanya 14 digit"),
    ]

    for token, desc in test_cases:
        is_16d, prov_valid, date_valid = validate_nik_structure(token)
        score = nik_structure_score(token)
        print(f"  {token:<20}  score={score:.2f}  ({desc})")

    # Test 3: Distribusi provinsi dari 1000 NIK
    print("\n[TEST 3] Distribusi provinsi (1000 NIK):")
    print("-" * 60)

    from collections import Counter
    rng2 = random.Random(42)
    prov_counter = Counter()

    for _ in range(1000):
        nik = generate_nik(rng2)
        prov_counter[int(nik[0:2])] += 1

    print(f"  Jumlah kode provinsi unik: {len(prov_counter)}/34")
    top5 = prov_counter.most_common(5)
    print(f"  Top 5 provinsi:")
    for code, count in top5:
        print(f"    {code:02d} - {VALID_PROVINCE_CODES[code]:<30}: {count}")

    # Test 4: Distribusi jenis kelamin
    print("\n[TEST 4] Distribusi jenis kelamin (1000 NIK):")
    print("-" * 60)

    rng3 = random.Random(42)
    laki = perempuan = 0

    for _ in range(1000):
        nik = generate_nik(rng3)
        tanggal = int(nik[6:8])
        if tanggal > 40:
            perempuan += 1
        else:
            laki += 1

    print(f"  Laki-laki  : {laki} ({laki/10:.1f}%)")
    print(f"  Perempuan  : {perempuan} ({perempuan/10:.1f}%)")

    print("\n" + "=" * 60)
    print("  Self-test selesai.")
    print("=" * 60)
