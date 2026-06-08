"""
================================================================
ANALYZER LOG MITMPROXY v2 — Fixed untuk format ndlp_addon
================================================================
Strategi yang benar:
1. Parse log per BLOK request (dipisahkan oleh "======")
2. Untuk setiap blok, ekstrak:
   - NIK pada "Original body" (yang diharapkan terdeteksi)
   - NIK pada baris "- NIK: <16d> -> <masked>" (yang BENAR terdeteksi)
3. Bandingkan kedua himpunan untuk hitung TP/FN dengan akurat
================================================================
"""

import json
import re
from pathlib import Path
import argparse


def parse_log_blocks(log_content: str) -> list:
    """
    Pecah log menjadi blok per request berdasarkan separator '====='.
    Setiap blok = satu intercepted request.
    """
    # Split berdasarkan garis pemisah yang muncul di log
    blocks = re.split(r"={50,}", log_content)
    # Filter blok kosong / hanya whitespace
    return [b.strip() for b in blocks if b.strip() and "Intercepted:" in b]


def extract_nik_from_block(block: str) -> dict:
    """
    Dari satu blok, ekstrak:
    - original_niks  : semua NIK 16-digit yang muncul di Original body
    - detected_niks  : NIK yang muncul di baris "- NIK: <16d> -> ..."
    - was_masked     : apakah ada baris "Masked body" yang menyebutkan XXXXXXXXXX
    """
    # NIK pada Original body: ambil 16-digit angka yang muncul di baris Original body
    original_niks = set()
    original_match = re.search(r"Original body:\s*(.+)", block)
    if original_match:
        original_text = original_match.group(1)
        # Cari semua 16-digit kontigu
        original_niks = set(re.findall(r"\b\d{16}\b", original_text))

    # NIK terdeteksi: pattern "- NIK: <16digit> -> <something>"
    detected_pattern = r"-\s*NIK:\s*(\d{16})\s*->\s*\S+"
    detected_niks = set(re.findall(detected_pattern, block))

    # Cek apakah blok ini benar-benar masked
    was_masked = "XXXXXXXXXX" in block or "Total" in block and "masked" in block

    # Latensi inferensi
    latency_match = re.search(r"Time:\s*([\d.]+)\s*ms", block)
    latency = float(latency_match.group(1)) if latency_match else None

    return {
        "original_niks": original_niks,
        "detected_niks": detected_niks,
        "was_masked": was_masked,
        "latency_ms": latency,
    }


def analyze_log(log_path: str, expected_niks: list) -> dict:
    """
    Hitung metrik validasi dengan benar:
    - TP = NIK yang dikirim DAN terdeteksi (muncul di baris "- NIK: ... ->")
    - FN = NIK yang dikirim TAPI tidak terdeteksi
    - FP = NIK yang TERDETEKSI tapi tidak ada di expected (seharusnya 0)
    """
    log_content = Path(log_path).read_text()
    blocks = parse_log_blocks(log_content)

    expected_set = set(expected_niks)

    # Agregat dari semua blok
    all_detected = set()
    blocks_with_nik = 0
    latencies = []
    per_request_results = []

    for i, block in enumerate(blocks, 1):
        info = extract_nik_from_block(block)

        # Hanya hitung blok yang memang membawa NIK kita
        relevant_originals = info["original_niks"] & expected_set
        if relevant_originals:
            blocks_with_nik += 1
            all_detected.update(info["detected_niks"])

            # Latensi
            if info["latency_ms"] is not None:
                latencies.append(info["latency_ms"])

            # Catat per request
            for nik in relevant_originals:
                per_request_results.append({
                    "nik": nik,
                    "detected": nik in info["detected_niks"],
                    "masked": info["was_masked"],
                    "latency_ms": info["latency_ms"],
                })

    # Hitung metrik
    tp = len(expected_set & all_detected)
    fn = len(expected_set - all_detected)
    fp = len(all_detected - expected_set)  # NIK terdeteksi yang bukan dari kita

    total = len(expected_set)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / total if total > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    # Statistik latensi
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0

    return {
        "total_blok_request": len(blocks),
        "blok_membawa_nik_uji": blocks_with_nik,
        "total_nik_diuji": total,
        "true_positive": tp,
        "false_negative": fn,
        "false_positive": fp,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "detection_rate_persen": round(recall * 100, 2),
        "latensi_inferensi": {
            "rata_rata_ms": round(avg_latency, 2),
            "minimum_ms": round(min_latency, 2),
            "maksimum_ms": round(max_latency, 2),
            "jumlah_sampel": len(latencies),
        },
        "nik_tidak_terdeteksi": sorted(list(expected_set - all_detected)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("log_path", help="Path ke file log mitmproxy")
    parser.add_argument("--niks", default="nik_valid_100.txt",
                        help="Path ke file daftar 100 NIK valid (default: nik_valid_100.txt)")
    args = parser.parse_args()

    # Load NIK yang diuji
    expected_niks = []
    with open(args.niks) as f:
        expected_niks = [line.strip() for line in f if line.strip()]

    print("=" * 60)
    print("VALIDASI 100 NIK VALID — ANALYZER v2 (FIXED)")
    print("=" * 60)
    print(f"Log file       : {args.log_path}")
    print(f"NIK reference  : {args.niks}")
    print(f"NIK terdaftar  : {len(expected_niks)}")
    print()

    result = analyze_log(args.log_path, expected_niks)

    # Output ringkasan
    print("HASIL ANALISIS:")
    print("-" * 60)
    print(f"  Total blok request di log        : {result['total_blok_request']}")
    print(f"  Blok yang membawa NIK uji        : {result['blok_membawa_nik_uji']}")
    print(f"  Total NIK diuji                  : {result['total_nik_diuji']}")
    print()
    print(f"  True Positive  (terdeteksi benar): {result['true_positive']}")
    print(f"  False Negative (lolos deteksi)   : {result['false_negative']}")
    print(f"  False Positive (deteksi salah)   : {result['false_positive']}")
    print()
    print(f"  Precision                        : {result['precision']}")
    print(f"  Recall                           : {result['recall']}")
    print(f"  F1-Score                         : {result['f1_score']}")
    print(f"  Detection Rate                   : {result['detection_rate_persen']}%")
    print()
    print("LATENSI INFERENSI:")
    lat = result["latensi_inferensi"]
    print(f"  Rata-rata                        : {lat['rata_rata_ms']} ms")
    print(f"  Minimum                          : {lat['minimum_ms']} ms")
    print(f"  Maksimum                         : {lat['maksimum_ms']} ms")
    print(f"  Sampel                           : {lat['jumlah_sampel']}")

    if result["nik_tidak_terdeteksi"]:
        print()
        print("NIK YANG LOLOS DETEKSI:")
        for nik in result["nik_tidak_terdeteksi"][:10]:
            print(f"  - {nik}")
        if len(result["nik_tidak_terdeteksi"]) > 10:
            print(f"  ... dan {len(result['nik_tidak_terdeteksi']) - 10} lainnya")

    print("=" * 60)

    # Simpan ke JSON
    with open("hasil_validasi_v2.json", "w") as f:
        json.dump(result, f, indent=2)
    print("Hasil lengkap tersimpan di: hasil_validasi_v2.json")


if __name__ == "__main__":
    main()
