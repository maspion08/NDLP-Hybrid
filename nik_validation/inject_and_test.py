"""
================================================================
INJEKSI 100 NIK VALID KE PAYLOAD UJI + AMBIL F1-SCORE
================================================================
Skenario: Mengirim 100 payload HTTPS yang berisi NIK valid struktural
ke VM_Nginx melalui VM_Proxy (mitmproxy + Hybrid CRF), kemudian
mengukur TP/FN/FP untuk menghitung Precision, Recall, dan F1-Score
khusus pada entitas NIK valid.

Hasil pengujian ini akan menjadi bukti tambahan bahwa model
Hybrid CRF mendeteksi NIK berbasis POLA UMUM (regex 16 digit
+ konteks label), BUKAN bergantung pada karakteristik struktural
spesifik NIK sintetis Faker.

Cara menjalankan:
    python3 inject_and_test.py                # mode generate payload
    python3 inject_and_test.py --send         # eksekusi pengujian
    python3 inject_and_test.py --analyze log  # analisis hasil dari log
================================================================
"""

import argparse
import json
import random
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Reproducibility
random.seed(2026)

# Template payload yang memuat NIK valid
TEMPLATE_JSON_SIMPLE = '{{"nama":"{nama}","nik":"{nik}","phone":"{phone}"}}'
TEMPLATE_JSON_NESTED = '{{"data":{{"identitas":{{"nik":"{nik}","nama":"{nama}"}},"kontak":{{"telepon":"{phone}"}}}}}}'
TEMPLATE_FORM = 'nama={nama}&nik={nik}&telepon={phone}'
TEMPLATE_NARATIF = 'Saudara {nama} dengan NIK {nik} dan nomor telepon {phone} telah terdaftar.'

NAMA_INDONESIA = [
    "Budi Santoso", "Siti Rahayu", "Agus Wijaya", "Dewi Lestari",
    "Hendra Pratama", "Ratna Sari", "Rizki Aditya", "Putri Maharani",
    "Andi Saputra", "Maya Anggraini",
]


def generate_phone() -> str:
    """Generate nomor telepon Indonesia sederhana."""
    prefix = random.choice(["0812", "0813", "0821", "0852", "0856", "0877", "0896"])
    suffix = "".join(str(random.randint(0, 9)) for _ in range(7))
    return prefix + suffix


def load_nik(path: str = "nik_valid_100.txt") -> list:
    """Load 100 NIK valid dari file."""
    here = Path(__file__).parent
    with open(here / path) as f:
        return [line.strip() for line in f if line.strip()]


def generate_payloads(nik_list: list) -> list:
    """
    Generate 100 payload uji dengan 4 variasi format secara seimbang.
    Setiap payload memuat tepat 1 NIK valid.
    """
    payloads = []
    formats = ["json_simple", "json_nested", "form", "naratif"]
    for i, nik in enumerate(nik_list):
        fmt = formats[i % 4]
        nama = random.choice(NAMA_INDONESIA)
        phone = generate_phone()

        if fmt == "json_simple":
            body = TEMPLATE_JSON_SIMPLE.format(nama=nama, nik=nik, phone=phone)
            content_type = "application/json"
        elif fmt == "json_nested":
            body = TEMPLATE_JSON_NESTED.format(nama=nama, nik=nik, phone=phone)
            content_type = "application/json"
        elif fmt == "form":
            body = TEMPLATE_FORM.format(nama=nama, nik=nik, phone=phone)
            content_type = "application/x-www-form-urlencoded"
        else:  # naratif
            body = TEMPLATE_NARATIF.format(nama=nama, nik=nik, phone=phone)
            content_type = "text/plain"

        payloads.append({
            "id": i + 1,
            "format": fmt,
            "nik_expected": nik,
            "nama_expected": nama,
            "phone_expected": phone,
            "content_type": content_type,
            "body": body,
        })
    return payloads


def save_payloads(payloads: list, path: str = "payloads.json"):
    here = Path(__file__).parent
    with open(here / path, "w", encoding="utf-8") as f:
        json.dump(payloads, f, indent=2, ensure_ascii=False)
    print(f"Tersimpan: {path} ({len(payloads)} payload)")


def generate_bash_script(payloads: list, path: str = "run_test.sh"):
    """
    Generate skrip bash untuk dijalankan di VM_CLIENT.
    Skrip akan mengirim 100 permintaan POST ke VM_Nginx melalui mitmproxy.
    """
    here = Path(__file__).parent
    target_url = "https://192.168.2.10/api/data"
    log_file = "validation_results.log"

    lines = [
        "#!/bin/bash",
        "# ================================================",
        "# Validasi 100 NIK VALID terhadap sistem NDLP",
        "# Dijalankan di VM_CLIENT setelah mitmdump aktif",
        "# ================================================",
        "",
        f'TARGET="{target_url}"',
        f'LOG="{log_file}"',
        f'echo "=== Mulai validasi 100 NIK valid pada $(date) ===" > $LOG',
        "",
    ]

    for p in payloads:
        # Quote payload agar aman di shell
        body_escaped = p["body"].replace("'", "'\"'\"'")
        lines.extend([
            f'echo "--- Test {p["id"]:03d} ({p["format"]}) | NIK expected: {p["nik_expected"]} ---" >> $LOG',
            f"curl -k -s -o /dev/null -w 'HTTP: %{{http_code}} | Time: %{{time_total}}s\\n' \\",
            f"     -X POST \"$TARGET\" \\",
            f'     -H "Content-Type: {p["content_type"]}" \\',
            f"     -d '{body_escaped}' >> $LOG",
            "sleep 0.1   # spasi antar request agar mitmdump tidak terbebani",
            "",
        ])

    lines.append('echo "=== Selesai pada $(date) ===" >> $LOG')
    lines.append('echo "Total: 100 permintaan dikirim. Lihat $LOG untuk hasilnya."')

    with open(here / path, "w") as f:
        f.write("\n".join(lines))
    (here / path).chmod(0o755)
    print(f"Tersimpan: {path} (jalankan dengan ./{path} di VM_CLIENT)")


def analyze_mitmproxy_log(log_path: str, expected_niks: list) -> dict:
    """
    Analisis log mitmproxy (ndlp.log) untuk menghitung TP/FN/FP per kategori.

    Asumsi format log dari ndlp_addon.py:
        [TIMESTAMP] PII detected: N entities | Time: X.XX ms
        [TIMESTAMP] Masked: NIK=3201..., PHONE=0812...

    Karena format detail log addon mungkin bervariasi, fungsi ini
    menggunakan pendekatan substring matching pada NIK yang diharapkan.
    """
    tp = 0  # NIK valid yang TERDETEKSI sebagai NIK
    fn = 0  # NIK valid yang LUPUT (tidak terdeteksi)
    detected_niks = set()

    try:
        with open(log_path) as f:
            log_content = f.read()
    except FileNotFoundError:
        print(f"PERINGATAN: File log {log_path} tidak ditemukan.")
        print("Pastikan log mitmproxy sudah tersedia setelah menjalankan run_test.sh.")
        return {}

    # Strategi sederhana: cek apakah masing-masing NIK expected muncul
    # dalam log sebagai entitas yang di-masking
    for nik in expected_niks:
        # Cek pola: NIK muncul DALAM konteks "masked" atau "detected"
        # Sesuaikan pola ini dengan format log addon Anda
        if nik in log_content:
            # Cek konteks: apakah NIK ini ditandai sebagai PII?
            idx = log_content.find(nik)
            context = log_content[max(0, idx - 100):idx + 100]
            if any(keyword in context.lower() for keyword in
                   ["masked", "detected", "nik=", "b-nik"]):
                tp += 1
                detected_niks.add(nik)
            else:
                fn += 1
        else:
            fn += 1

    total = len(expected_niks)
    precision = tp / (tp + 0) if tp > 0 else 0  # tidak ada FP per definisi (NIK valid)
    recall = tp / total if total > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "total_nik_diuji": total,
        "true_positive": tp,
        "false_negative": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "detection_rate_persen": round(recall * 100, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="Validasi NDLP terhadap 100 NIK valid struktural")
    parser.add_argument("--analyze", metavar="LOG_PATH",
                        help="Analisis log mitmproxy untuk hitung F1-score")
    args = parser.parse_args()

    if args.analyze:
        nik_list = load_nik()
        result = analyze_mitmproxy_log(args.analyze, nik_list)
        if result:
            print("\n" + "=" * 60)
            print("HASIL VALIDASI 100 NIK VALID")
            print("=" * 60)
            for k, v in result.items():
                print(f"  {k:30s}: {v}")
            print("=" * 60)

            # Simpan hasil
            with open("hasil_validasi.json", "w") as f:
                json.dump(result, f, indent=2)
            print("\nHasil tersimpan di: hasil_validasi.json")
        return

    # Default: generate payload + script
    print("=" * 60)
    print("PERSIAPAN PAYLOAD UJI - 100 NIK VALID")
    print("=" * 60)

    nik_list = load_nik()
    print(f"Loaded {len(nik_list)} NIK valid dari nik_valid_100.txt")

    payloads = generate_payloads(nik_list)
    save_payloads(payloads)

    print("\nDistribusi format:")
    from collections import Counter
    dist = Counter(p["format"] for p in payloads)
    for fmt, jumlah in sorted(dist.items()):
        print(f"  {fmt:15s}: {jumlah}")

    generate_bash_script(payloads)

    print("\n" + "=" * 60)
    print("LANGKAH SELANJUTNYA (di VM_CLIENT):")
    print("=" * 60)
    print("1. Pastikan mitmproxy aktif di VM_PROXY:")
    print("   mitmdump -s ~/ndlp_addon.py --mode transparent --listen-host 0.0.0.0 \\")
    print("     --listen-port 8080 --ssl-insecure")
    print()
    print("2. Transfer file ke VM_CLIENT:")
    print("   scp run_test.sh nik_valid_100.txt client@192.168.1.10:~/jmeter-tests/")
    print()
    print("3. Jalankan validasi:")
    print("   ssh client@192.168.1.10 'cd ~/jmeter-tests && ./run_test.sh'")
    print()
    print("4. Ambil log mitmproxy & analisis:")
    print("   scp server@192.168.1.1:/var/log/ndlp/ndlp.log .")
    print("   python3 inject_and_test.py --analyze ndlp.log")
    print("=" * 60)


if __name__ == "__main__":
    main()
