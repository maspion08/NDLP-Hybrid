"""
Validasi Dataset Enriched (Combined + Adversarial + Held-Out)
Tugas Akhir: Arga Ariyuda Avian (2221101774)
"""
import os
import sys
import pandas as pd
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def validate_combined():
    """Validate combined dataset"""
    print("="*70)
    print("  🔍 VALIDATING COMBINED DATASET (Training)")
    print("="*70)
    
    path = 'data/processed/dataset_combined_bio.pkl'
    if not os.path.exists(path):
        print(f"  ❌ File not found: {path}")
        return False
    
    df = pd.read_pickle(path)
    checks = []
    
    # Check 1: Total
    expected = 11000
    c1 = len(df) == expected
    checks.append(c1)
    print(f"  {'✅' if c1 else '❌'} Total: {len(df)} (expected {expected})")
    
    # Check 2: Source distribution
    if 'source' in df.columns:
        src_dist = df['source'].value_counts().to_dict()
        c2 = src_dist.get('main', 0) == 10000 and src_dist.get('adversarial', 0) == 1000
        checks.append(c2)
        print(f"  {'✅' if c2 else '❌'} Source: {src_dist}")
    
    # Check 3: Token-Label alignment
    aligned = df.apply(lambda r: len(r['tokens']) == len(r['labels']), axis=1).all()
    checks.append(aligned)
    print(f"  {'✅' if aligned else '❌'} Token-Label alignment: {aligned}")
    
    # Check 4: Valid label set
    valid = {'O', 'B-NIK', 'B-PHONE', 'B-NAMA', 'I-NAMA',
             'B-JABATAN', 'I-JABATAN', 'B-LOKASI', 'I-LOKASI'}
    all_labels = set()
    for labels in df['labels']:
        all_labels.update(labels)
    invalid = all_labels - valid
    c4 = len(invalid) == 0
    checks.append(c4)
    print(f"  {'✅' if c4 else '❌'} Valid label set: {invalid if invalid else 'All valid'}")
    
    return all(checks)


def validate_splits():
    """Validate train/val/test splits"""
    print("\n" + "="*70)
    print("  🔍 VALIDATING TRAIN/VAL/TEST SPLITS")
    print("="*70)
    
    files = {
        'train': ('data/processed/train.pkl', 8800),  # 80% of 11000
        'val': ('data/processed/val.pkl', 1100),       # 10%
        'test': ('data/processed/test.pkl', 1100),     # 10%
    }
    
    checks = []
    for name, (path, expected) in files.items():
        if not os.path.exists(path):
            print(f"  ❌ {path} not found")
            checks.append(False)
            continue
        
        df = pd.read_pickle(path)
        # Allow 1-2 sample variance due to integer rounding in stratification
        c = abs(len(df) - expected) <= 2
        checks.append(c)
        print(f"  {'✅' if c else '❌'} {name}: {len(df)} samples (expected ~{expected})")
    
    return all(checks)


def validate_holdout():
    """Validate held-out test set"""
    print("\n" + "="*70)
    print("  🔍 VALIDATING HELD-OUT TEST SET")
    print("="*70)
    
    path = 'data/test_holdout/naturalistic_bio.pkl'
    if not os.path.exists(path):
        print(f"  ❌ File not found: {path}")
        return False
    
    df = pd.read_pickle(path)
    checks = []
    
    # Check 1: Total
    c1 = len(df) == 1000
    checks.append(c1)
    print(f"  {'✅' if c1 else '❌'} Total: {len(df)} (expected 1000)")
    
    # Check 2: Token-Label alignment
    aligned = df.apply(lambda r: len(r['tokens']) == len(r['labels']), axis=1).all()
    checks.append(aligned)
    print(f"  {'✅' if aligned else '❌'} Token-Label alignment: {aligned}")
    
    # Check 3: Format diversity (7 formats)
    formats = df['format'].unique()
    c3 = len(formats) == 7
    checks.append(c3)
    print(f"  {'✅' if c3 else '❌'} Format diversity: {len(formats)} formats - {sorted(formats)}")
    
    # Check 4: Detection coverage
    print(f"\n  📊 Holdout entity detection coverage:")
    coverage_ok = True
    for entity in ['NIK', 'PHONE', 'NAMA', 'JABATAN', 'LOKASI']:
        b_label = f'B-{entity}'
        detected = df['labels'].apply(lambda x: b_label in x).sum()
        rate = (detected/len(df))*100
        is_ok = rate >= 80  # More lenient for naturalistic
        if not is_ok:
            coverage_ok = False
        status = '✅' if rate >= 95 else ('⚠️ ' if rate >= 80 else '❌')
        print(f"     {status} {entity:<10}: {detected}/{len(df)} ({rate:.1f}%)")
    
    checks.append(coverage_ok)
    return all(checks)


def main():
    combined_ok = validate_combined()
    splits_ok = validate_splits()
    holdout_ok = validate_holdout()
    
    print("\n" + "="*70)
    print("  🎯 FINAL VERDICT")
    print("="*70)
    
    if combined_ok and splits_ok and holdout_ok:
        print("  ✅ ALL VALIDATIONS PASSED")
        print("  ➡️  Dataset enriched ready for re-training")
        print("\n  📋 Next steps:")
        print("     1. Re-train Regex (no change expected, baseline)")
        print("     2. Re-train HMM (will be tested on enriched test)")
        print("     3. Re-train CRF (F1 should drop from 1.00 to ~0.92)")
        print("     4. Train Hybrid HMM (NEW)")
        print("     5. Train Hybrid CRF (NEW)")
        print("     6. Evaluate ALL on holdout (1000 naturalistic)")
    else:
        failed = []
        if not combined_ok: failed.append("COMBINED")
        if not splits_ok: failed.append("SPLITS")
        if not holdout_ok: failed.append("HOLDOUT")
        print(f"  ❌ Failed: {', '.join(failed)}")
    
    print("="*70)


if __name__ == "__main__":
    main()