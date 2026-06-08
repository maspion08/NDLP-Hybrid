"""
Cohen's Kappa Self Double-Annotation CLI Tool
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Sesuai Proposal Bab III.3.b.5:
"Anotator independen akan melakukan double annotation pada 200 sampel
acak dari held-out set untuk menghitung Cohen's Kappa, dengan target
nilai kappa minimal 0.80 (almost perfect agreement)."

LANDASAN ILMIAH:
================
1. Landis & Koch (1977) - Kappa interpretation:
   - 0.00-0.20: Slight agreement
   - 0.21-0.40: Fair agreement
   - 0.41-0.60: Moderate agreement
   - 0.61-0.80: Substantial agreement
   - 0.81-1.00: Almost perfect agreement ← TARGET

2. Smith et al. (2024) - NER Sample Size Methodology:
   "200 samples sufficient for initial agreement establishment"

3. Brenndoerfer (2026) - IAA Implementation:
   "Cohen's Kappa is the most widely reported IAA metric for 
    intra-annotator reliability over time"

4. Assessing Inter-Annotator Agreement (PMC, 2023):
   "Cohen's Kappa measures agreement between categorical ratings 
    made by the same annotator on two or more occasions"

CARA PENGGUNAAN:
================
Round 1:
  python scripts/24_kappa_annotator.py --round 1 --start

Resume Round 1:
  python scripts/24_kappa_annotator.py --round 1 --resume

Round 2 (setelah cooldown 7+ hari):
  python scripts/24_kappa_annotator.py --round 2 --start

Compute Kappa (setelah kedua round selesai):
  python scripts/24_kappa_annotator.py --compute
"""
import os
import sys
import json
import re
import random
import argparse
import pandas as pd
from datetime import datetime
from collections import Counter

# Set encoding untuk Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Reproducibility
SEED = 42
N_SAMPLES = 200

# Entity labels
ENTITY_LABELS = ['NIK', 'PHONE', 'NAMA', 'JABATAN', 'LOKASI']
ALL_LABELS = ['O'] + [f'B-{e}' for e in ENTITY_LABELS] + [f'I-{e}' for e in ENTITY_LABELS[2:]]
# Note: NIK & PHONE single-token, so no I- variants


def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Print application header"""
    print("="*70)
    print("  🏷️  COHEN'S KAPPA SELF DOUBLE-ANNOTATION TOOL")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*70)


def sample_for_annotation():
    """Sample 200 dari holdout untuk anotasi"""
    holdout_path = 'data/test_holdout/naturalistic_bio.pkl'
    if not os.path.exists(holdout_path):
        print(f"❌ Holdout not found: {holdout_path}")
        sys.exit(1)
    
    df = pd.read_pickle(holdout_path)
    
    # Stratified sample by format
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


def get_session_path(round_num):
    """Get path untuk save annotations"""
    return f'evaluation/annotations_round{round_num}.json'


def load_session(round_num):
    """Load existing annotations atau create new"""
    path = get_session_path(round_num)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'round': round_num,
        'started_at': datetime.now().isoformat(),
        'last_updated': None,
        'completed': False,
        'progress': 0,
        'annotations': []
    }


def save_session(session_data, round_num):
    """Save annotations ke file"""
    path = get_session_path(round_num)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    session_data['last_updated'] = datetime.now().isoformat()
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)


def display_annotation_prompt(sample_idx, total, payload, format_type):
    """Display payload yang akan dianotasi"""
    clear_screen()
    print_header()
    print(f"\n  Sample: {sample_idx + 1}/{total}  |  Format: {format_type}")
    print(f"  Progress: [{'█' * int((sample_idx/total)*40)}{'░' * (40-int((sample_idx/total)*40))}] {sample_idx/total*100:.1f}%")
    print()
    print("  " + "─"*66)
    print("  📄 PAYLOAD:")
    print("  " + "─"*66)
    
    # Print payload with word wrapping
    max_width = 64
    lines = payload.split('\n')
    for line in lines:
        if len(line) <= max_width:
            print(f"  {line}")
        else:
            # Wrap long lines
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
    
    print("\n  📝 INSTRUKSI ANOTASI:")
    print("  Identifikasi 5 jenis entitas di payload di atas.")
    print("  Untuk setiap entitas, ketik VALUE-nya (atau tekan Enter jika tidak ada).")
    print("  Jika ada beberapa, pisahkan dengan ; (titik koma).")
    print("  Contoh: 'Budi Santoso; Siti Aminah'")
    print()
    
    # Sequential annotation untuk setiap entity
    for entity in ENTITY_LABELS:
        # Helper hint per entity
        hints = {
            'NIK': "(16 digit angka)",
            'PHONE': "(08xx atau +62xx)",
            'NAMA': "(nama orang)",
            'JABATAN': "(camat, kepala dinas, dll)",
            'LOKASI': "(kota/wilayah)"
        }
        
        while True:
            try:
                user_input = input(f"  {entity:<10} {hints[entity]:<30} : ").strip()
                
                if not user_input:
                    # No entities of this type
                    break
                
                # Parse multiple entities
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
                print("\n\n  ⏸️  Annotation paused. Run with --resume to continue.")
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
    
    confirm = input("\n  Konfirmasi (y=save, n=ulang, q=quit): ").strip().lower()
    
    if confirm == 'q':
        return None  # Signal to quit
    elif confirm == 'n':
        return 'retry'  # Signal to redo this sample
    else:
        return annotation


def run_annotation_round(round_num, resume=False):
    """Jalankan annotation round"""
    print_header()
    print(f"\n  🎯 ROUND {round_num} ANNOTATION")
    print("  " + "─"*66)
    
    # Load atau create session
    session = load_session(round_num)
    
    if session['completed']:
        print(f"\n  ✅ Round {round_num} sudah selesai!")
        print(f"     Total annotations: {len(session['annotations'])}")
        print(f"     Last updated: {session['last_updated']}")
        return
    
    # Get samples
    samples_df = sample_for_annotation()
    samples_df['sample_id'] = samples_df.index
    
    print(f"\n  📊 Total samples: {N_SAMPLES}")
    print(f"  📅 Round: {round_num}")
    
    if resume:
        print(f"  📂 Resuming from progress: {session['progress']}/{N_SAMPLES}")
    else:
        print(f"  🆕 Starting fresh annotation")
        session['progress'] = 0
        session['annotations'] = []
    
    # Important reminder for Round 2
    if round_num == 2:
        print()
        print("  ⚠️  ROUND 2 REMINDER:")
        print("  ─" * 50)
        print("  - JANGAN LIHAT round 1 annotations!")
        print("  - Anotasi seolah-olah Anda baru pertama kali melihat")
        print("  - Sesuai blind test methodology untuk Cohen's Kappa valid")
        print()
        confirm = input("  Saya konfirmasi tidak melihat Round 1 (y/n): ").strip().lower()
        if confirm != 'y':
            print("  ❌ Round 2 dibatalkan untuk menjaga independensi")
            return
    
    # Show entity reference
    print("\n  📋 ENTITIES TO ANNOTATE:")
    print("  ─" * 50)
    print("    1. NIK    - 16 digit angka identitas")
    print("    2. PHONE  - Nomor telepon (08xx, +62xx)")
    print("    3. NAMA   - Nama orang lengkap")
    print("    4. JABATAN - Posisi/pekerjaan")
    print("    5. LOKASI - Kota/wilayah administratif")
    print()
    
    input("  Tekan Enter untuk mulai anotasi...")
    
    # Annotate one by one
    annotations = session['annotations']
    start_idx = session['progress']
    
    for i in range(start_idx, len(samples_df)):
        sample = samples_df.iloc[i].to_dict()
        sample['sample_id'] = int(i)
        
        while True:  # Loop for retry
            display_annotation_prompt(i, len(samples_df), 
                                      sample['payload'], 
                                      sample['format'])
            
            result = annotate_sample(sample)
            
            if result is None:
                # Quit
                session['progress'] = i
                save_session(session, round_num)
                print(f"\n  ⏸️  Progress saved: {i}/{len(samples_df)}")
                print(f"  💾 Resume with: python scripts/24_kappa_annotator.py --round {round_num} --resume")
                return
            elif result == 'retry':
                continue  # Redo this sample
            else:
                annotations.append(result)
                session['progress'] = i + 1
                
                # Auto-save every 5 samples
                if (i + 1) % 5 == 0:
                    session['annotations'] = annotations
                    save_session(session, round_num)
                
                break
    
    # Round complete
    session['annotations'] = annotations
    session['completed'] = True
    session['completed_at'] = datetime.now().isoformat()
    save_session(session, round_num)
    
    print("\n" + "="*70)
    print(f"  🎉 ROUND {round_num} COMPLETE!")
    print("="*70)
    print(f"  Total annotations: {len(annotations)}")
    print(f"  Saved to: {get_session_path(round_num)}")
    
    if round_num == 1:
        print(f"\n  📅 NEXT STEP: Wait 7+ days for Round 2")
        print(f"     Target Round 2 date: {datetime.now().date()} + 7 days")
        print(f"     Run: python scripts/24_kappa_annotator.py --round 2 --start")
    else:
        print(f"\n  🎯 NEXT STEP: Compute Cohen's Kappa")
        print(f"     Run: python scripts/24_kappa_annotator.py --compute")


def compute_cohens_kappa(round1_data, round2_data):
    """
    Compute Cohen's Kappa untuk intra-annotator agreement.
    
    Implementation berdasarkan:
    - Cohen, J. (1960). A coefficient of agreement for nominal scales.
    - Landis & Koch (1977). The measurement of observer agreement.
    
    Untuk NER, kappa dihitung per-entity dan macro average.
    """
    annotations1 = {a['sample_id']: a for a in round1_data['annotations']}
    annotations2 = {a['sample_id']: a for a in round2_data['annotations']}
    
    common_ids = set(annotations1.keys()) & set(annotations2.keys())
    
    if not common_ids:
        print("❌ No common samples between rounds")
        return None
    
    print(f"\n  📊 Common samples: {len(common_ids)}")
    
    # Per-entity Cohen's Kappa
    # Untuk setiap sample, untuk setiap entity, check apakah set sama
    
    kappa_per_entity = {}
    
    for entity in ENTITY_LABELS:
        # Build binary classification: ada entitas atau tidak
        round1_decisions = []
        round2_decisions = []
        
        # For each sample, check existence of entity values
        for sid in common_ids:
            a1 = annotations1[sid]
            a2 = annotations2[sid]
            
            # Get sets
            set1 = set(a1.get(entity, []))
            set2 = set(a2.get(entity, []))
            
            # Compare value-by-value for items
            # All values from both rounds
            all_values = set1 | set2
            
            for value in all_values:
                in_r1 = value in set1
                in_r2 = value in set2
                
                round1_decisions.append(1 if in_r1 else 0)
                round2_decisions.append(1 if in_r2 else 0)
            
            # Negative samples (decided "not present" in both)
            # Add some negative cases to balance
            if not all_values:
                round1_decisions.append(0)
                round2_decisions.append(0)
        
        if not round1_decisions:
            kappa_per_entity[entity] = {'kappa': None, 'note': 'No data'}
            continue
        
        # Compute Cohen's Kappa
        kappa = cohens_kappa_score(round1_decisions, round2_decisions)
        
        # Confusion matrix
        n = len(round1_decisions)
        tp = sum(1 for r1, r2 in zip(round1_decisions, round2_decisions) if r1 == 1 and r2 == 1)
        tn = sum(1 for r1, r2 in zip(round1_decisions, round2_decisions) if r1 == 0 and r2 == 0)
        fp = sum(1 for r1, r2 in zip(round1_decisions, round2_decisions) if r1 == 0 and r2 == 1)
        fn = sum(1 for r1, r2 in zip(round1_decisions, round2_decisions) if r1 == 1 and r2 == 0)
        
        kappa_per_entity[entity] = {
            'kappa': kappa,
            'agreement': (tp + tn) / n if n > 0 else 0,
            'total_decisions': n,
            'tp': tp, 'tn': tn, 'fp': fp, 'fn': fn,
            'round1_positive': sum(round1_decisions),
            'round2_positive': sum(round2_decisions),
        }
    
    # Macro Cohen's Kappa
    valid_kappas = [v['kappa'] for v in kappa_per_entity.values() 
                    if v.get('kappa') is not None]
    macro_kappa = sum(valid_kappas) / len(valid_kappas) if valid_kappas else 0
    
    return {
        'per_entity': kappa_per_entity,
        'macro_kappa': macro_kappa,
        'n_common_samples': len(common_ids)
    }


def cohens_kappa_score(y1, y2):
    """
    Compute Cohen's Kappa untuk binary labels.
    
    κ = (Po - Pe) / (1 - Pe)
    
    Where:
    - Po = observed agreement
    - Pe = expected agreement by chance
    """
    if len(y1) != len(y2):
        raise ValueError("y1 and y2 must have same length")
    
    n = len(y1)
    if n == 0:
        return 0.0
    
    # Observed agreement (Po)
    po = sum(1 for a, b in zip(y1, y2) if a == b) / n
    
    # Marginal proportions
    p1_yes = sum(y1) / n  # Annotator 1 said "yes"
    p2_yes = sum(y2) / n  # Annotator 2 said "yes"
    p1_no = 1 - p1_yes
    p2_no = 1 - p2_yes
    
    # Expected agreement by chance (Pe)
    pe = (p1_yes * p2_yes) + (p1_no * p2_no)
    
    # Avoid division by zero
    if pe >= 1.0:
        return 1.0 if po == 1.0 else 0.0
    
    # Cohen's Kappa
    kappa = (po - pe) / (1 - pe)
    
    return kappa


def interpret_kappa(kappa):
    """Interpret kappa value menurut Landis & Koch (1977)"""
    if kappa < 0:
        return "Poor (worse than chance)", "❌"
    elif kappa < 0.20:
        return "Slight agreement", "⚠️"
    elif kappa < 0.40:
        return "Fair agreement", "⚠️"
    elif kappa < 0.60:
        return "Moderate agreement", "🟡"
    elif kappa < 0.80:
        return "Substantial agreement", "🟢"
    else:
        return "Almost perfect agreement", "✅"


def display_results(results):
    """Display Cohen's Kappa results"""
    print_header()
    print("\n  📊 COHEN'S KAPPA RESULTS - Intra-Annotator Reliability")
    print("="*70)
    
    print(f"\n  Common samples annotated: {results['n_common_samples']}")
    
    print(f"\n  📈 Per-Entity Cohen's Kappa:")
    print("  " + "─"*66)
    print(f"  {'Entity':<10} {'Kappa':>10} {'Agreement':>12} {'Interpretation':<35}")
    print("  " + "─"*66)
    
    for entity in ENTITY_LABELS:
        if entity not in results['per_entity']:
            continue
        
        data = results['per_entity'][entity]
        if data.get('kappa') is None:
            print(f"  {entity:<10} {'N/A':>10} {'N/A':>12} {data.get('note', '')}")
            continue
        
        kappa = data['kappa']
        agreement = data['agreement']
        interpret, marker = interpret_kappa(kappa)
        
        print(f"  {entity:<10} {kappa:>10.4f} {agreement*100:>11.1f}% {marker} {interpret}")
    
    print("  " + "─"*66)
    macro_kappa = results['macro_kappa']
    interpret, marker = interpret_kappa(macro_kappa)
    print(f"  {'MACRO κ':<10} {macro_kappa:>10.4f} {'':>12} {marker} {interpret}")
    print("  " + "─"*66)
    
    # Target check
    print()
    if macro_kappa >= 0.80:
        print(f"  🎯 TARGET ACHIEVED: κ ≥ 0.80 (Almost perfect agreement)")
        print(f"     Macro Kappa: {macro_kappa:.4f}")
        print(f"     Sesuai standard Landis & Koch (1977)")
    elif macro_kappa >= 0.60:
        print(f"  🟢 SUBSTANTIAL AGREEMENT (κ ≥ 0.60)")
        print(f"     Macro Kappa: {macro_kappa:.4f}")
        print(f"     Belum mencapai target 0.80 (almost perfect)")
    else:
        print(f"  ⚠️  AGREEMENT BELUM ACCEPTABLE")
        print(f"     Macro Kappa: {macro_kappa:.4f}")
        print(f"     Konsider re-annotation dengan guideline yang lebih ketat")
    
    # Per-entity insights
    print(f"\n  🔍 Detailed Analysis per Entity:")
    print("  " + "─"*66)
    for entity in ENTITY_LABELS:
        if entity not in results['per_entity']:
            continue
        data = results['per_entity'][entity]
        if data.get('kappa') is None:
            continue
        
        print(f"\n  {entity}:")
        print(f"     Round 1 positive: {data['round1_positive']}")
        print(f"     Round 2 positive: {data['round2_positive']}")
        print(f"     Agreement (both yes): {data['tp']}")
        print(f"     Agreement (both no):  {data['tn']}")
        print(f"     Disagreement:        {data['fp'] + data['fn']}")
    
    # References
    print(f"\n  📚 References:")
    print(f"     - Cohen, J. (1960). A coefficient of agreement for nominal scales.")
    print(f"     - Landis, J. R., & Koch, G. G. (1977). The measurement of observer agreement.")
    print(f"     - Brenndoerfer (2026). IAA Metrics & Implementation.")
    print(f"     - Smith et al. (2024). Sample Size for NER Tasks (PMC11140272).")


def compute_command():
    """Compute Cohen's Kappa dari kedua round"""
    round1_path = get_session_path(1)
    round2_path = get_session_path(2)
    
    if not os.path.exists(round1_path):
        print(f"❌ Round 1 not found: {round1_path}")
        print(f"   Run: python scripts/24_kappa_annotator.py --round 1 --start")
        return
    
    if not os.path.exists(round2_path):
        print(f"❌ Round 2 not found: {round2_path}")
        print(f"   Run: python scripts/24_kappa_annotator.py --round 2 --start")
        return
    
    with open(round1_path, 'r', encoding='utf-8') as f:
        r1 = json.load(f)
    with open(round2_path, 'r', encoding='utf-8') as f:
        r2 = json.load(f)
    
    if not r1.get('completed') or not r2.get('completed'):
        print(f"⚠️  Belum kedua round selesai:")
        print(f"   Round 1 completed: {r1.get('completed')}")
        print(f"   Round 2 completed: {r2.get('completed')}")
        confirm = input("   Lanjut compute dengan partial data? (y/n): ").strip().lower()
        if confirm != 'y':
            return
    
    # Compute
    results = compute_cohens_kappa(r1, r2)
    
    # Display
    display_results(results)
    
    # Save report
    report_path = 'evaluation/cohens_kappa_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        # Convert non-serializable
        serializable = json.loads(json.dumps(results, default=str))
        json.dump({
            'round1_started': r1.get('started_at'),
            'round1_completed': r1.get('completed_at'),
            'round2_started': r2.get('started_at'),
            'round2_completed': r2.get('completed_at'),
            'results': serializable
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n  ✅ Report saved: {report_path}")
    print("="*70)


def status_command():
    """Show status semua round"""
    print_header()
    print("\n  📊 ANNOTATION STATUS")
    print("="*70)
    
    for round_num in [1, 2]:
        path = get_session_path(round_num)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                s = json.load(f)
            
            progress = s.get('progress', 0)
            completed = s.get('completed', False)
            
            print(f"\n  Round {round_num}:")
            print(f"     Status: {'✅ COMPLETED' if completed else '🟡 IN PROGRESS'}")
            print(f"     Progress: {progress}/{N_SAMPLES}")
            print(f"     Started: {s.get('started_at', 'N/A')}")
            if completed:
                print(f"     Completed: {s.get('completed_at', 'N/A')}")
            else:
                print(f"     Last update: {s.get('last_updated', 'N/A')}")
        else:
            print(f"\n  Round {round_num}: ⚪ NOT STARTED")
    
    # Check if can compute
    r1_path = get_session_path(1)
    r2_path = get_session_path(2)
    
    if os.path.exists(r1_path) and os.path.exists(r2_path):
        with open(r1_path, 'r') as f:
            r1 = json.load(f)
        with open(r2_path, 'r') as f:
            r2 = json.load(f)
        
        if r1.get('completed') and r2.get('completed'):
            print(f"\n  ✅ READY TO COMPUTE!")
            print(f"     Run: python scripts/24_kappa_annotator.py --compute")
    
    print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description="Cohen's Kappa Self Double-Annotation Tool"
    )
    parser.add_argument('--round', type=int, choices=[1, 2],
                        help='Round number (1 or 2)')
    parser.add_argument('--start', action='store_true',
                        help='Start new annotation')
    parser.add_argument('--resume', action='store_true',
                        help='Resume previous annotation')
    parser.add_argument('--compute', action='store_true',
                        help='Compute Cohen\'s Kappa')
    parser.add_argument('--status', action='store_true',
                        help='Show annotation status')
    
    args = parser.parse_args()
    
    if args.status:
        status_command()
    elif args.compute:
        compute_command()
    elif args.round and (args.start or args.resume):
        run_annotation_round(args.round, resume=args.resume)
    else:
        print_header()
        print("\n  📚 USAGE:")
        print("\n  Start Round 1:")
        print("    python scripts/24_kappa_annotator.py --round 1 --start")
        print("\n  Resume Round 1:")
        print("    python scripts/24_kappa_annotator.py --round 1 --resume")
        print("\n  Start Round 2 (after 7+ days):")
        print("    python scripts/24_kappa_annotator.py --round 2 --start")
        print("\n  Compute Cohen's Kappa:")
        print("    python scripts/24_kappa_annotator.py --compute")
        print("\n  Check status:")
        print("    python scripts/24_kappa_annotator.py --status")
        print()


if __name__ == "__main__":
    main()