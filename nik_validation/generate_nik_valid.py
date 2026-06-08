"""
================================================================
GENERATOR NIK VALID SESUAI STRUKTUR DUKCAPIL
================================================================
Tugas Akhir: Arga Ariyuda Avian (2221101774)
Politeknik Siber dan Sandi Negara

Tujuan:
    Menghasilkan 100 NIK sintetis yang memenuhi SELURUH kaidah
    struktural NIK resmi Indonesia berdasarkan Permendagri No. 19/2010
    dan informasi resmi Disdukcapil:

    Struktur 16 digit NIK = PP KK CC DDMMYY NNNN
    - PP   : Kode provinsi (11-94, hanya yang valid)
    - KK   : Kode kota/kabupaten (01-99)
    - CC   : Kode kecamatan (01-99)
    - DD   : Tanggal lahir (laki: 01-31; perempuan: tanggal+40 = 41-71)
    - MM   : Bulan lahir (01-12)
    - YY   : Dua digit terakhir tahun lahir
    - NNNN : Nomor urut penerbitan (0001-9999)

CATATAN PRIVASI:
    NIK yang digenerate adalah SINTETIS dan TIDAK terkait dengan
    warga negara Indonesia manapun. Generator menggunakan kombinasi
    acak komponen sehingga tidak menciptakan identitas spesifik.
================================================================
"""

import random
import json
import csv
from datetime import datetime
from pathlib import Path

# Reproducibility
RANDOM_SEED = 2026
random.seed(RANDOM_SEED)

# ============================================================
# REFERENSI: KODE PROVINSI VALID (Permendagri No. 137/2017)
# ============================================================
# Hanya kode provinsi yang valid (skip kode yang tidak dipakai)
KODE_PROVINSI_VALID = {
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

# ============================================================
# HELPER: Hitung tanggal maksimum per bulan (handle Februari)
# ============================================================
def hari_dalam_bulan(bulan: int, tahun_4digit: int) -> int:
    """Mengembalikan jumlah hari valid dalam suatu bulan-tahun."""
    if bulan in (1, 3, 5, 7, 8, 10, 12):
        return 31
    if bulan in (4, 6, 9, 11):
        return 30
    # Februari: cek tahun kabisat
    if (tahun_4digit % 4 == 0 and tahun_4digit % 100 != 0) or (tahun_4digit % 400 == 0):
        return 29
    return 28


def generate_nik_valid(jenis_kelamin: str = None, tahun_min: int = 1960,
                       tahun_max: int = 2005) -> dict:
    """
    Generate 1 NIK 16 digit yang VALID secara struktural.

    Args:
        jenis_kelamin: 'L' (laki), 'P' (perempuan), atau None (acak)
        tahun_min, tahun_max: rentang tahun lahir (default usia produktif 2026)

    Returns:
        dict berisi NIK dan metadata strukturnya
    """
    # 1. Kode Wilayah (6 digit)
    kode_prov = random.choice(list(KODE_PROVINSI_VALID.keys()))
    kode_kab = random.randint(1, 99)       # 01-99
    kode_kec = random.randint(1, 99)       # 01-99

    # 2. Jenis kelamin
    if jenis_kelamin is None:
        jenis_kelamin = random.choice(['L', 'P'])

    # 3. Tanggal lahir
    tahun_lahir = random.randint(tahun_min, tahun_max)
    bulan_lahir = random.randint(1, 12)
    max_tgl = hari_dalam_bulan(bulan_lahir, tahun_lahir)
    tanggal_riil = random.randint(1, max_tgl)

    # 4. Encoding tanggal pada NIK
    # Laki-laki  : DD apa adanya (01-31)
    # Perempuan : DD + 40 (41-71)
    if jenis_kelamin == 'L':
        tanggal_nik = tanggal_riil
    else:
        tanggal_nik = tanggal_riil + 40

    # 5. Dua digit tahun
    yy = tahun_lahir % 100

    # 6. Nomor urut penerbitan (0001-9999)
    nomor_urut = random.randint(1, 9999)

    # 7. Susun NIK 16 digit
    nik = (
        f"{kode_prov:02d}"
        f"{kode_kab:02d}"
        f"{kode_kec:02d}"
        f"{tanggal_nik:02d}"
        f"{bulan_lahir:02d}"
        f"{yy:02d}"
        f"{nomor_urut:04d}"
    )

    # Validasi panjang
    assert len(nik) == 16, f"NIK harus 16 digit, tetapi terdapat {len(nik)} digit: {nik}"
    assert nik.isdigit(), f"NIK harus angka semua: {nik}"

    return {
        "nik": nik,
        "kode_provinsi": f"{kode_prov:02d}",
        "nama_provinsi": KODE_PROVINSI_VALID[kode_prov],
        "kode_kabupaten": f"{kode_kab:02d}",
        "kode_kecamatan": f"{kode_kec:02d}",
        "tanggal_lahir": f"{tahun_lahir}-{bulan_lahir:02d}-{tanggal_riil:02d}",
        "tanggal_pada_nik": f"{tanggal_nik:02d}",
        "bulan_pada_nik": f"{bulan_lahir:02d}",
        "tahun_pada_nik": f"{yy:02d}",
        "nomor_urut": f"{nomor_urut:04d}",
        "jenis_kelamin": jenis_kelamin,
    }


def validate_nik_structure(nik: str) -> dict:
    """
    Validasi apakah suatu NIK memenuhi seluruh kaidah struktural.
    Digunakan untuk verifikasi hasil generate.
    """
    if len(nik) != 16 or not nik.isdigit():
        return {"valid": False, "alasan": "Panjang bukan 16 digit atau bukan angka"}

    kode_prov = int(nik[0:2])
    if kode_prov not in KODE_PROVINSI_VALID:
        return {"valid": False, "alasan": f"Kode provinsi {kode_prov} tidak valid"}

    tanggal = int(nik[6:8])
    bulan = int(nik[8:10])
    yy = int(nik[10:12])

    if bulan < 1 or bulan > 12:
        return {"valid": False, "alasan": f"Bulan {bulan} tidak valid (harus 1-12)"}

    # Tanggal: laki 1-31, perempuan 41-71
    if tanggal >= 41:
        tanggal_riil = tanggal - 40
        jenis_kelamin = "P"
    else:
        tanggal_riil = tanggal
        jenis_kelamin = "L"

    if tanggal_riil < 1 or tanggal_riil > 31:
        return {"valid": False, "alasan": f"Tanggal {tanggal_riil} tidak valid"}

    # Validasi tanggal sesuai bulan (kabisat dll)
    tahun_4digit = 2000 + yy if yy < 26 else 1900 + yy  # asumsi cutoff 2026
    if tanggal_riil > hari_dalam_bulan(bulan, tahun_4digit):
        return {
            "valid": False,
            "alasan": f"Tanggal {tanggal_riil} tidak valid untuk bulan {bulan} tahun {tahun_4digit}"
        }

    return {
        "valid": True,
        "provinsi": KODE_PROVINSI_VALID[kode_prov],
        "jenis_kelamin": jenis_kelamin,
        "tanggal_lahir": f"{tahun_4digit}-{bulan:02d}-{tanggal_riil:02d}",
    }


# ============================================================
# MAIN: Generate 100 NIK valid
# ============================================================
if __name__ == "__main__":
    JUMLAH = 100
    nik_list = []
    laki = 0
    perempuan = 0

    print("=" * 60)
    print(f"GENERATOR NIK VALID - {JUMLAH} sampel")
    print(f"Random seed: {RANDOM_SEED}")
    print("=" * 60)

    for i in range(JUMLAH):
        entry = generate_nik_valid()
        nik_list.append(entry)
        if entry["jenis_kelamin"] == "L":
            laki += 1
        else:
            perempuan += 1

    # Self-test: pastikan SEMUA hasil generate valid struktural
    print(f"\nVerifikasi struktural seluruh {JUMLAH} NIK ...")
    invalid_count = 0
    for entry in nik_list:
        check = validate_nik_structure(entry["nik"])
        if not check["valid"]:
            invalid_count += 1
            print(f"  GAGAL: {entry['nik']} -> {check['alasan']}")
    if invalid_count == 0:
        print(f"  Hasil: SEMUA {JUMLAH} NIK lulus validasi struktural ✓")

    # Statistik distribusi
    print(f"\nDistribusi:")
    print(f"  Laki-laki : {laki}")
    print(f"  Perempuan : {perempuan}")
    print(f"  Provinsi unik: {len(set(e['kode_provinsi'] for e in nik_list))}/34")

    # Output 1: JSON lengkap dengan metadata
    output_dir = Path(__file__).parent
    with open(output_dir / "nik_valid_100.json", "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "jumlah": JUMLAH,
                "random_seed": RANDOM_SEED,
                "generated_at": datetime.now().isoformat(),
                "deskripsi": "100 NIK sintetis valid struktural untuk validasi tambahan TA NDLP",
                "rentang_tahun_lahir": "1960-2005",
                "distribusi_jenis_kelamin": {"L": laki, "P": perempuan},
            },
            "data": nik_list,
        }, f, indent=2, ensure_ascii=False)

    # Output 2: TXT (NIK saja, satu per baris untuk injeksi cepat)
    with open(output_dir / "nik_valid_100.txt", "w", encoding="utf-8") as f:
        for entry in nik_list:
            f.write(entry["nik"] + "\n")

    # Output 3: CSV untuk inspeksi manual di Excel
    with open(output_dir / "nik_valid_100.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["NIK", "Provinsi", "Tanggal Lahir", "Jenis Kelamin", "Nomor Urut"])
        for entry in nik_list:
            writer.writerow([
                entry["nik"], entry["nama_provinsi"], entry["tanggal_lahir"],
                entry["jenis_kelamin"], entry["nomor_urut"],
            ])

    # Sample 5 NIK pertama
    print(f"\nContoh 5 NIK pertama:")
    print("-" * 60)
    for entry in nik_list[:5]:
        print(f"  {entry['nik']}  |  {entry['nama_provinsi']:25s}  |  "
              f"{entry['tanggal_lahir']}  |  {entry['jenis_kelamin']}")

    print("\n" + "=" * 60)
    print("OUTPUT FILES:")
    print("  - nik_valid_100.json  (metadata lengkap)")
    print("  - nik_valid_100.txt   (NIK saja, satu per baris)")
    print("  - nik_valid_100.csv   (untuk inspeksi manual)")
    print("=" * 60)
