"""
Inter-Annotator Annotation Tool - untuk Annotator B (Novi)
Tugas Akhir: Arga Ariyuda Avian (2221101774)

TUJUAN:
=======
Tool untuk Annotator B (Novi) melakukan anotasi independen pada 200 
sampel SAMA yang sudah diannotasi oleh Annotator A (Arga).
Hasilnya akan dibandingkan untuk menghitung Inter-Annotator Cohen's Kappa.

LANDASAN ILMIAH:
================
1. Landis & Koch (1977) - Kappa interpretation:
   - 0.00-0.20: Slight agreement
   - 0.21-0.40: Fair agreement
   - 0.41-0.60: Moderate agreement
   - 0.61-0.80: Substantial agreement
   - 0.81-1.00: Almost perfect agreement ← TARGET

CARA PENGGUNAAN (untuk Novi):
==============================
Mulai anotasi:
  python scripts/30_annotator_novi.py --start

Resume anotasi (kalau berhenti di tengah):
  python scripts/30_annotator_novi.py --resume

Cek status:
  python scripts/30_annotator_novi.py --status
"""
import os
import sys
import json
import argparse
import pandas as pd
from datetime import datetime

# Set encoding untuk Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Konfigurasi - HARUS SAMA dengan annotator A
SEED = 42
N_SAMPLES = 200
ANNOTATOR_NAME = "Novi"
ANNOTATOR_ROLE = "Annotator B (Independent)"

# Entity labels
ENTITY_LABELS = ['NIK', 'PHONE', 'NAMA', 'JABATAN', 'LOKASI']

# Path konfigurasi
SESSION_PATH = 'evaluation/annotations_novi.json'


def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Print application header"""
    print("="*70)
    print("  🏷️  INTER-ANNOTATOR ANNOTATION TOOL")
    print(f"  Annotator: {ANNOTATOR_NAME} ({ANNOTATOR_ROLE})")
    print("  Penelitian TA: Arga Ariyuda Avian (2221101774)")
    print("="*70)


def sample_for_annotation():
    """
    Sample 200 dari holdout - HARUS SAMA dengan Annotator A
    Menggunakan SEED yang sama untuk reproducibility.
    """
    holdout_path = 'data/test_holdout/naturalistic_bio.pkl'
    if not os.path.exists(holdout_path):
        print(f"❌ Holdout not found: {holdout_path}")
        sys.exit(1)
    
    df = pd.read_pickle(holdout_path)
    
    # Stratified sample by format - PERSIS SAMA dengan script Arga
    samples = []
    formats = df['format'].unique()
    samples_per_format = N_SAMPLES // len(formats)
    extra = N_SAMPLES - (samples_per_format * len(formats))
    
    for i, fmt in enumerate(sorted(formats)):
        fmt_df = df[df['format'] == fmt]
        n = samples_per_format + (1 if i < extra else 0)
        fmt_samples = fmt_df.sample(n=min(n, len(fmt_df)), random_state=SEED)
        samples.append(fmt_samples)
    
    sampled = pd.concat(samples, ignore_index=True)
    sampled = sampled.sample(frac=1, random_state=SEED).reset_index(drop=True)
    
    return sampled.head(N_SAMPLES)


def load_session():
    """Load existing annotations atau create new"""
    if os.path.exists(SESSION_PATH):
        with open(SESSION_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'annotator': ANNOTATOR_NAME,
        'role': ANNOTATOR_ROLE,
        'started_at': datetime.now().isoformat(),
        'last_updated': None,
        'completed': False,
        'progress': 0,
        'annotations': []
    }


def save_session(session_data):
    """Save annotations ke file"""
    os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)
    session_data['last_updated'] = datetime.now().isoformat()
    
    with open(SESSION_PATH, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)


def display_annotation_prompt(sample_idx, total, payload, format_type):
    """Display payload yang akan dianotasi"""
    clear_screen()
    print_header()
    print(f"\n  Sample: {sample_idx + 1}/{total}  |  Format: {format_type}")
    progress_pct = (sample_idx/total)*100
    bar_filled = int((sample_idx/total)*40)
    print(f"  Progress: [{'█' * bar_filled}{'░' * (40-bar_filled)}] {progress_pct:.1f}%")
    print()
    print("  " + "─"*66)
    print("  📄 PAYLOAD (teks yang harus dianotasi):")
    print("  " + "─"*66)
    
    # Print payload with word wrapping
    max_width = 64
    lines = payload.split('\n')
    for line in lines:
        if len(line) <= max_width:
            print(f"  {line}")
        else:
            for i in range(0, len(line), max_width):
                print(f"  {line[i:i+max_width]}")
    
    print("  " + "─"*66)


def annotate_sample(sample):
    """Anotasi 1 sample, return dict entitas yang ditemukan"""
    payload = sample['payload']
    format_type = sample['format']
    
    annotation = {
        'sample_id': sample['sample_id'],
        'format': format_type,
        'NIK': [],
        'PHONE': [],
        'NAMA': [],
        'JABATAN': [],
        'LOKASI': [],
        'note': ''
    }
    
    print("\n  📝 INSTRUKSI:")
    print("  Identifikasi 5 jenis entitas di payload di atas.")
    print("  Ketik VALUE-nya (atau tekan Enter jika tidak ada).")
    print("  Jika ada beberapa, pisahkan dengan ; (titik koma).")
    print("  Contoh: 'Budi Santoso; Siti Aminah'")
    print()
    
    # Hint per entity
    hints = {
        'NIK': "(16 digit angka)",
        'PHONE': "(08xx atau +62xx)",
        'NAMA': "(nama orang)",
        'JABATAN': "(camat, kepala dinas, dll)",
        'LOKASI': "(kota/wilayah)"
    }
    
    # Sequential annotation untuk setiap entity
    for entity in ENTITY_LABELS:
        while True:
            try:
                user_input = input(f"  {entity:<10} {hints[entity]:<30} : ").strip()
                
                if not user_input:
                    break
                
                values = [v.strip() for v in user_input.split(';') if v.strip()]
                
                # Validate: check if values exist in payload
                invalid = []
                for v in values:
                    if v not in payload:
                        invalid.append(v)
                
                if invalid:
                    print(f"  ⚠️  Warning: tidak ditemukan di payload:")
                    for v in invalid:
                        print(f"      - '{v}'")
                    confirm = input("  Lanjut anyway? (y/n): ").strip().lower()
                    if confirm != 'y':
                        continue
                
                annotation[entity] = values
                break
            
            except KeyboardInterrupt:
                print("\n\n  ⏸️  Annotasi pause. Resume dengan: --resume")
                return None
    
    # Optional note
    note = input(f"\n  💭 Catatan tambahan (Enter untuk skip): ").strip()
    if note:
        annotation['note'] = note
    
    # Confirmation
    print("\n  ✅ Anotasi:")
    for entity in ENTITY_LABELS:
        if annotation[entity]:
            print(f"     {entity}: {', '.join(annotation[entity])}")
        else:
            print(f"     {entity}: (kosong)")
    
    confirm = input("\n  Konfirmasi (y=save, n=ulang, q=quit): ").strip().lower()
    
    if confirm == 'q':
        return None
    elif confirm == 'n':
        return 'retry'
    else:
        return annotation


def run_annotation(resume=False):
    """Jalankan annotation untuk Novi"""
    print_header()
    print("\n  🎯 INTER-ANNOTATOR ANNOTATION")
    print("  " + "─"*66)
    
    # Load atau create session
    session = load_session()
    
    if session['completed']:
        print(f"\n  ✅ Anotasi sudah selesai!")
        print(f"     Total annotations: {len(session['annotations'])}")
        print(f"     Last updated: {session['last_updated']}")
        return
    
    # Get samples - SAMA dengan annotator A
    samples_df = sample_for_annotation()
    samples_df['sample_id'] = samples_df.index
    
    print(f"\n  📊 Total samples: {N_SAMPLES}")
    print(f"  👤 Annotator: {ANNOTATOR_NAME}")
    
    if resume:
        print(f"  📂 Resume dari progress: {session['progress']}/{N_SAMPLES}")
    else:
        print(f"  🆕 Mulai anotasi baru")
        session['progress'] = 0
        session['annotations'] = []
    
    # PENTING: Reminder independence
    print()
    print("  ⚠️  PENTING - REMINDER:")
    print("  ─" * 50)
    print("  • JANGAN melihat anotasi Arga sebelum selesai")
    print("  • Anotasi secara INDEPENDEN sesuai pemahamanmu")
    print("  • Ini untuk Inter-Annotator Agreement (Cohen's Kappa)")
    print("  • Konsistensi lebih penting daripada 'benar' atau 'salah'")
    print()
    confirm = input("  Saya konfirmasi tidak melihat anotasi Arga (y/n): ").strip().lower()
    if confirm != 'y':
        print("  ❌ Anotasi dibatalkan untuk menjaga independensi")
        return
    
    # Show entity reference
    print("\n  📋 5 ENTITAS YANG DIANOTASI:")
    print("  ─" * 50)
    print("    1. NIK     - 16 digit angka (HATI-HATI: bukan Order ID!)")
    print("    2. PHONE   - Nomor telepon (08xx, +62xx)")
    print("    3. NAMA    - Nama orang lengkap (termasuk gelar)")
    print("    4. JABATAN - Posisi/pekerjaan formal (Camat, Lurah, dll)")
    print("    5. LOKASI  - Kota/wilayah administratif")
    print()
    print("  💡 Cek panduan lengkap di: PANDUAN_NOVI.md")
    print()
    
    input("  Tekan Enter untuk mulai anotasi...")
    
    # Annotate one by one
    annotations = session['annotations']
    start_idx = session['progress']
    
    for i in range(start_idx, len(samples_df)):
        sample = samples_df.iloc[i].to_dict()
        sample['sample_id'] = int(i)
        
        while True:
            display_annotation_prompt(i, len(samples_df), 
                                      sample['payload'], 
                                      sample['format'])
            
            result = annotate_sample(sample)
            
            if result is None:
                # Quit
                session['progress'] = i
                save_session(session)
                print(f"\n  ⏸️  Progress saved: {i}/{len(samples_df)}")
                print(f"  💾 Resume dengan: python scripts/30_annotator_novi.py --resume")
                return
            elif result == 'retry':
                continue
            else:
                annotations.append(result)
                session['progress'] = i + 1
                
                # Auto-save tiap 5 sampel
                if (i + 1) % 5 == 0:
                    session['annotations'] = annotations
                    save_session(session)
                
                break
    
    # Complete
    session['annotations'] = annotations
    session['completed'] = True
    session['completed_at'] = datetime.now().isoformat()
    save_session(session)
    
    print("\n" + "="*70)
    print(f"  🎉 ANOTASI SELESAI!")
    print("="*70)
    print(f"  Annotator: {ANNOTATOR_NAME}")
    print(f"  Total annotations: {len(annotations)}")
    print(f"  Saved to: {SESSION_PATH}")
    print(f"\n  ⏭️  NEXT STEP (untuk Arga):")
    print(f"     1. Backup file annotations_novi.json")
    print(f"     2. Hitung Inter-Annotator Cohen's Kappa")
    print(f"     3. Run: python scripts/31_compute_inter_kappa.py")
    print("="*70)


def status_command():
    """Show annotation status"""
    print_header()
    print("\n  📊 ANNOTATION STATUS")
    print("="*70)
    
    if os.path.exists(SESSION_PATH):
        with open(SESSION_PATH, 'r', encoding='utf-8') as f:
            s = json.load(f)
        
        progress = s.get('progress', 0)
        completed = s.get('completed', False)
        
        print(f"\n  Annotator: {s.get('annotator', 'Unknown')}")
        print(f"  Status: {'✅ COMPLETED' if completed else '🟡 IN PROGRESS'}")
        print(f"  Progress: {progress}/{N_SAMPLES}")
        print(f"  Started: {s.get('started_at', 'N/A')}")
        if completed:
            print(f"  Completed: {s.get('completed_at', 'N/A')}")
        else:
            print(f"  Last update: {s.get('last_updated', 'N/A')}")
            remaining = N_SAMPLES - progress
            print(f"  Remaining: {remaining} samples")
    else:
        print(f"\n  Status: ⚪ NOT STARTED")
        print(f"  Run: python scripts/30_annotator_novi.py --start")
    
    print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description="Inter-Annotator Annotation Tool for Novi"
    )
    parser.add_argument('--start', action='store_true',
                        help='Start anotasi baru')
    parser.add_argument('--resume', action='store_true',
                        help='Resume anotasi sebelumnya')
    parser.add_argument('--status', action='store_true',
                        help='Cek status anotasi')
    
    args = parser.parse_args()
    
    if args.status:
        status_command()
    elif args.start or args.resume:
        run_annotation(resume=args.resume)
    else:
        print_header()
        print("\n  📚 USAGE:")
        print("\n  Mulai anotasi:")
        print("    python scripts/30_annotator_novi.py --start")
        print("\n  Resume anotasi (kalau berhenti):")
        print("    python scripts/30_annotator_novi.py --resume")
        print("\n  Cek status:")
        print("    python scripts/30_annotator_novi.py --status")
        print()


if __name__ == "__main__":
    main()