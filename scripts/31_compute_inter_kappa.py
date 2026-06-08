"""
Compute Inter-Annotator Cohen's Kappa
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Membandingkan:
- Arga (Round 1):  evaluation/annotations_round1.json
- Novi:             evaluation/annotations_novi.json

Output: Cohen's Kappa per entity dan macro average
"""
import os
import sys
import json
import pandas as pd
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

ENTITY_LABELS = ['NIK', 'PHONE', 'NAMA', 'JABATAN', 'LOKASI']


def cohens_kappa_score(y1, y2):
    """Compute Cohen's Kappa untuk binary labels"""
    if len(y1) != len(y2):
        raise ValueError("y1 and y2 must have same length")
    
    n = len(y1)
    if n == 0:
        return 0.0
    
    po = sum(1 for a, b in zip(y1, y2) if a == b) / n
    
    p1_yes = sum(y1) / n
    p2_yes = sum(y2) / n
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


def compute_inter_kappa(arga_data, novi_data):
    """Compute Cohen's Kappa antara Arga dan Novi"""
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
        arga_decisions = []
        novi_decisions = []
        entity_disagreements = []
        
        for sid in common_ids:
            a_arga = arga_anns[sid]
            a_novi = novi_anns[sid]
            
            set_arga = set(a_arga.get(entity, []))
            set_novi = set(a_novi.get(entity, []))
            
            all_values = set_arga | set_novi
            
            for value in all_values:
                in_arga = value in set_arga
                in_novi = value in set_novi
                
                arga_decisions.append(1 if in_arga else 0)
                novi_decisions.append(1 if in_novi else 0)
                
                if in_arga != in_novi:
                    entity_disagreements.append({
                        'sample_id': sid,
                        'value': value,
                        'in_arga': in_arga,
                        'in_novi': in_novi
                    })
            
            if not all_values:
                arga_decisions.append(0)
                novi_decisions.append(0)
        
        if not arga_decisions:
            kappa_per_entity[entity] = {'kappa': None, 'note': 'No data'}
            continue
        
        kappa = cohens_kappa_score(arga_decisions, novi_decisions)
        
        n = len(arga_decisions)
        tp = sum(1 for a, b in zip(arga_decisions, novi_decisions) if a == 1 and b == 1)
        tn = sum(1 for a, b in zip(arga_decisions, novi_decisions) if a == 0 and b == 0)
        fp = sum(1 for a, b in zip(arga_decisions, novi_decisions) if a == 0 and b == 1)
        fn = sum(1 for a, b in zip(arga_decisions, novi_decisions) if a == 1 and b == 0)
        
        kappa_per_entity[entity] = {
            'kappa': kappa,
            'agreement': (tp + tn) / n if n > 0 else 0,
            'total_decisions': n,
            'tp': tp, 'tn': tn, 'fp': fp, 'fn': fn,
            'arga_positive': sum(arga_decisions),
            'novi_positive': sum(novi_decisions),
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
    print("  📊 INTER-ANNOTATOR COHEN'S KAPPA RESULTS")
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
        print(f"     Arga annotated  : {data['arga_positive']}")
        print(f"     Novi annotated  : {data['novi_positive']}")
        print(f"     Both agreed YES : {data['tp']}")
        print(f"     Both agreed NO  : {data['tn']}")
        print(f"     Disagreement    : {data['fp'] + data['fn']}")
    
    # Sample disagreements
    print(f"\n  ❓ Sample Disagreements (top 5 per entity):")
    print("  " + "─"*66)
    for entity in ENTITY_LABELS:
        if entity in results.get('disagreements', {}) and results['disagreements'][entity]:
            print(f"\n  {entity}:")
            for d in results['disagreements'][entity][:5]:
                arga_mark = "✓" if d['in_arga'] else "✗"
                novi_mark = "✓" if d['in_novi'] else "✗"
                print(f"     [{d['sample_id']:3d}] '{d['value']}' - Arga:{arga_mark} Novi:{novi_mark}")


def main():
    print("="*70)
    print("  🧮 COMPUTING INTER-ANNOTATOR COHEN'S KAPPA")
    print("="*70)
    
    # Load Arga's annotations
    arga_path = 'evaluation/annotations_round1.json'
    if not os.path.exists(arga_path):
        print(f"\n❌ Arga annotations not found: {arga_path}")
        sys.exit(1)
    
    with open(arga_path, 'r', encoding='utf-8') as f:
        arga_data = json.load(f)
    
    print(f"\n📂 Loaded Arga (Round 1): {len(arga_data['annotations'])} annotations")
    
    # Load Novi's annotations
    novi_path = 'evaluation/annotations_novi.json'
    if not os.path.exists(novi_path):
        print(f"\n❌ Novi annotations not found: {novi_path}")
        print(f"   Belum kerjain? Run: python scripts/30_annotator_novi.py --start")
        sys.exit(1)
    
    with open(novi_path, 'r', encoding='utf-8') as f:
        novi_data = json.load(f)
    
    print(f"📂 Loaded Novi: {len(novi_data['annotations'])} annotations")
    
    if not novi_data.get('completed'):
        progress = novi_data.get('progress', 0)
        print(f"\n⚠️  Novi belum selesai (progress: {progress}/200)")
        confirm = input("   Lanjut compute dengan partial data? (y/n): ").strip().lower()
        if confirm != 'y':
            sys.exit(0)
    
    # Compute
    results = compute_inter_kappa(arga_data, novi_data)
    
    if results is None:
        sys.exit(1)
    
    # Display
    display_results(results, arga_data, novi_data)
    
    # Save report
    os.makedirs('evaluation', exist_ok=True)
    report_path = 'evaluation/inter_annotator_kappa_report.json'
    
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