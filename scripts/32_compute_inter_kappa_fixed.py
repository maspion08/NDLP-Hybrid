"""
Compute Inter-Annotator Cohen's Kappa (FIXED VERSION)
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Perbaikan:
- Menghitung True Negatives (TN) secara akurat berbasis jumlah token pada teks.
- Menggunakan matrix TP, TN, FP, FN secara langsung.
"""
import os
import sys
import json
import pandas as pd
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

ENTITY_LABELS = ['NIK', 'PHONE', 'NAMA', 'JABATAN', 'LOKASI']

def compute_kappa_from_confusion(tp, tn, fp, fn):
    """Compute Cohen's Kappa langsung dari confusion matrix"""
    n = tp + tn + fp + fn
    if n == 0:
        return 0.0
    
    po = (tp + tn) / n
    p1_yes = (tp + fn) / n
    p2_yes = (tp + fp) / n
    p1_no = 1 - p1_yes
    p2_no = 1 - p2_yes
    
    pe = (p1_yes * p2_yes) + (p1_no * p2_no)
    
    if pe >= 1.0:
        return 1.0 if po == 1.0 else 0.0
    
    return (po - pe) / (1 - pe)


def interpret_kappa(kappa):
    """Landis & Koch (1977) interpretation"""
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


def compute_inter_kappa(arga_data, novi_data, payloads_dict):
    """Compute Cohen's Kappa antara Arga dan Novi dengan perhitungan TN valid"""
    arga_anns = {a['sample_id']: a for a in arga_data['annotations']}
    novi_anns = {a['sample_id']: a for a in novi_data['annotations']}
    
    common_ids = set(arga_anns.keys()) & set(novi_anns.keys())
    
    if not common_ids:
        print("❌ Tidak ada sampel yang sama!")
        return None
    
    print(f"\n  📊 Common samples: {len(common_ids)}")
    
    kappa_per_entity = {}
    disagreements = {}
    
    for entity in ENTITY_LABELS:
        tp = tn = fp = fn = 0
        entity_disagreements = []
        arga_positive_count = 0
        novi_positive_count = 0
        
        for sid in common_ids:
            a_arga = arga_anns[sid]
            a_novi = novi_anns[sid]
            
            set_arga = set(a_arga.get(entity, []))
            set_novi = set(a_novi.get(entity, []))
            
            # Hitung True Positives, False Positives, False Negatives
            sample_tp = len(set_arga & set_novi)
            sample_fp = len(set_novi - set_arga)
            sample_fn = len(set_arga - set_novi)
            
            tp += sample_tp
            fp += sample_fp
            fn += sample_fn
            arga_positive_count += len(set_arga)
            novi_positive_count += len(set_novi)
            
            # Estimasi total token (kata) di payload dokumen ini
            payload = payloads_dict.get(sid, "")
            total_tokens = len(payload.split())
            if total_tokens == 0:
                total_tokens = 50 # Fallback safety
            
            # True Negatives = Sisa kata yang disepakati BUKAN entitas
            sample_tn = max(0, total_tokens - (sample_tp + sample_fp + sample_fn))
            tn += sample_tn
            
            # Catat Disagreements
            all_values = set_arga | set_novi
            for value in all_values:
                in_arga = value in set_arga
                in_novi = value in set_novi
                if in_arga != in_novi:
                    entity_disagreements.append({
                        'sample_id': sid,
                        'value': value,
                        'in_arga': in_arga,
                        'in_novi': in_novi
                    })
        
        n_decisions = tp + tn + fp + fn
        if n_decisions == 0:
            kappa_per_entity[entity] = {'kappa': None, 'note': 'No data'}
            continue
            
        kappa = compute_kappa_from_confusion(tp, tn, fp, fn)
        
        kappa_per_entity[entity] = {
            'kappa': kappa,
            'agreement': (tp + tn) / n_decisions if n_decisions > 0 else 0,
            'total_decisions': n_decisions,
            'tp': tp, 'tn': tn, 'fp': fp, 'fn': fn,
            'arga_positive': arga_positive_count,
            'novi_positive': novi_positive_count,
        }
        
        disagreements[entity] = entity_disagreements
    
    valid_kappas = [v['kappa'] for v in kappa_per_entity.values() 
                    if v.get('kappa') is not None]
    macro_kappa = sum(valid_kappas) / len(valid_kappas) if valid_kappas else 0
    
    return {
        'per_entity': kappa_per_entity,
        'macro_kappa': macro_kappa,
        'n_common_samples': len(common_ids),
        'disagreements': disagreements
    }


def display_results(results, arga_data, novi_data):
    """Display hasil Cohen's Kappa"""
    print("="*70)
    print("  📊 INTER-ANNOTATOR COHEN'S KAPPA RESULTS (FIXED)")
    print("="*70)
    
    print(f"\n  Annotator A: Arga Ariyuda Avian (Peneliti)")
    print(f"  Annotator B: Novi (Independent Annotator)")
    print(f"  Common samples: {results['n_common_samples']}")
    
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
    
    print()
    if macro_kappa >= 0.80:
        print(f"  🎯 TARGET TERCAPAI: κ ≥ 0.80 (Almost perfect agreement)")
        print(f"     Macro Kappa: {macro_kappa:.4f}")
    elif macro_kappa >= 0.60:
        print(f"  🟢 SUBSTANTIAL AGREEMENT (κ ≥ 0.60)")
        print(f"     Macro Kappa: {macro_kappa:.4f}")
    else:
        print(f"  ⚠️  Agreement belum optimal")
        print(f"     Macro Kappa: {macro_kappa:.4f}")
    
    print(f"\n  🔍 Detailed Analysis per Entity:")
    print("  " + "─"*66)
    for entity in ENTITY_LABELS:
        if entity not in results['per_entity']:
            continue
        data = results['per_entity'][entity]
        if data.get('kappa') is None:
            continue
        
        print(f"\n  {entity}:")
        print(f"     Arga found     : {data['arga_positive']}")
        print(f"     Novi found     : {data['novi_positive']}")
        print(f"     Both agreed YES: {data['tp']}")
        print(f"     Both agreed NO : {data['tn']}")
        print(f"     Disagreement   : {data['fp'] + data['fn']}")


def main():
    print("="*70)
    print("  🧮 COMPUTING INTER-ANNOTATOR COHEN'S KAPPA (FIXED)")
    print("="*70)
    
    # 1. Load Original Payloads untuk menghitung kata
    holdout_path = 'data/test_holdout/naturalistic_bio.pkl'
    payloads_dict = {}
    if os.path.exists(holdout_path):
        df = pd.read_pickle(holdout_path)
        payloads_dict = dict(zip(df.index, df['payload']))
        print(f"📂 Loaded Original Dataset: {len(payloads_dict)} payloads untuk TN calc")
    else:
        print(f"\n❌ Original dataset not found: {holdout_path}")
        sys.exit(1)
        
    # 2. Load Arga's annotations
    arga_path = 'evaluation/annotations_round1.json'
    if not os.path.exists(arga_path):
        print(f"\n❌ Arga annotations not found: {arga_path}")
        sys.exit(1)
    
    with open(arga_path, 'r', encoding='utf-8') as f:
        arga_data = json.load(f)
    print(f"📂 Loaded Arga (Round 1): {len(arga_data['annotations'])} annotations")
    
    # 3. Load Novi's annotations
    novi_path = 'evaluation/annotations_novi.json'
    if not os.path.exists(novi_path):
        print(f"\n❌ Novi annotations not found: {novi_path}")
        sys.exit(1)
    
    with open(novi_path, 'r', encoding='utf-8') as f:
        novi_data = json.load(f)
    print(f"📂 Loaded Novi: {len(novi_data['annotations'])} annotations")
    
    # 4. Compute & Display
    results = compute_inter_kappa(arga_data, novi_data, payloads_dict)
    
    if results is None:
        sys.exit(1)
        
    display_results(results, arga_data, novi_data)
    
    # Save report
    os.makedirs('evaluation', exist_ok=True)
    report_path = 'evaluation/inter_annotator_kappa_report_fixed.json'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        serializable = json.loads(json.dumps(results, default=str))
        json.dump({
            'annotator_a': 'Arga Ariyuda Avian',
            'annotator_b': 'Novi',
            'arga_completed': arga_data.get('completed_at'),
            'novi_completed': novi_data.get('completed_at'),
            'computed_at': datetime.now().isoformat(),
            'results': serializable
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n  ✅ Report saved: {report_path}")
    print("="*70)

if __name__ == "__main__":
    main()