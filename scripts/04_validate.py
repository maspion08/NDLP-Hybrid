"""
Comprehensive Dataset Validation
Tugas Akhir: Arga Ariyuda Avian (2221101774)
"""
import os
import json
import pandas as pd
from collections import Counter


def validate_raw():
    """Validate raw dataset"""
    print("="*65)
    print("  🔍 RAW DATASET VALIDATION")
    print("="*65)
    
    path = 'data/raw/dataset_raw.pkl'
    if not os.path.exists(path):
        print(f"  ❌ File not found: {path}")
        return False
    
    df = pd.read_pickle(path)
    checks = []
    
    # Total
    c1 = len(df) == 10000
    checks.append(c1)
    print(f"  {'✅' if c1 else '❌'} Total: {len(df)} (expected 10000)")
    
    # Distribution
    expected = {'json': 4000, 'formdata': 4000, 'narrative': 1500, 'negative': 500}
    actual = df['format'].value_counts().to_dict()
    c2 = actual == expected
    checks.append(c2)
    print(f"  {'✅' if c2 else '❌'} Distribution: {actual}")
    
    # No nulls
    c3 = df['payload'].isnull().sum() == 0
    checks.append(c3)
    print(f"  {'✅' if c3 else '❌'} No null payloads")
    
    # PII complete for non-negative
    non_neg = df[df['format'] != 'negative']
    c4 = non_neg['pii_data'].notna().sum() == len(non_neg)
    checks.append(c4)
    print(f"  {'✅' if c4 else '❌'} PII data complete")
    
    # JSON validity
    sample = df[df['format'] == 'json'].iloc[0]['payload']
    try:
        json.loads(sample)
        c5 = True
    except:
        c5 = False
    checks.append(c5)
    print(f"  {'✅' if c5 else '❌'} JSON format valid")
    
    return all(checks)


def validate_bio():
    """Validate BIO-tagged dataset"""
    print("\n" + "="*65)
    print("  🔍 BIO DATASET VALIDATION")
    print("="*65)
    
    path = 'data/processed/dataset_bio.pkl'
    if not os.path.exists(path):
        print(f"  ❌ File not found: {path}")
        return False
    
    df = pd.read_pickle(path)
    checks = []
    
    # Token-Label alignment
    aligned = df.apply(lambda r: len(r['tokens']) == len(r['labels']), axis=1).all()
    checks.append(aligned)
    print(f"  {'✅' if aligned else '❌'} Token-Label alignment: {aligned}")
    
    # Valid label set
    valid = {'O', 'B-NIK', 'B-PHONE', 'B-NAMA', 'I-NAMA',
             'B-JABATAN', 'I-JABATAN', 'B-LOKASI', 'I-LOKASI'}
    all_labels = set()
    for labels in df['labels']:
        all_labels.update(labels)
    invalid = all_labels - valid
    c2 = len(invalid) == 0
    checks.append(c2)
    print(f"  {'✅' if c2 else '❌'} Valid label set: {invalid if invalid else 'All valid'}")
    
    # BIO consistency
    inconsistent = 0
    for labels in df['labels']:
        for i, label in enumerate(labels):
            if label.startswith('I-'):
                entity = label[2:]
                if i == 0:
                    inconsistent += 1
                else:
                    prev = labels[i-1]
                    if not (prev == f'B-{entity}' or prev == f'I-{entity}'):
                        inconsistent += 1
    c3 = inconsistent == 0
    checks.append(c3)
    print(f"  {'✅' if c3 else '❌'} BIO consistency: {inconsistent} violations")
    
    # Negative all-O
    neg_df = df[df['format'] == 'negative']
    c4 = neg_df['labels'].apply(lambda x: all(l == 'O' for l in x)).all()
    checks.append(c4)
    print(f"  {'✅' if c4 else '❌'} Negative samples all-O")
    
    # Detection coverage
    print(f"\n  📊 Detection coverage:")
    coverage_ok = True
    for entity in ['NIK', 'PHONE', 'NAMA', 'JABATAN', 'LOKASI']:
        b_label = f'B-{entity}'
        non_neg = df[df['format'] != 'negative']
        detected = non_neg['labels'].apply(lambda x: b_label in x).sum()
        total = len(non_neg)
        rate = (detected/total)*100
        is_ok = rate >= 95
        if not is_ok:
            coverage_ok = False
        status = '✅' if rate >= 99 else ('⚠️ ' if rate >= 95 else '❌')
        print(f"     {status} {entity:<10}: {detected}/{total} ({rate:.1f}%)")
    
    checks.append(coverage_ok)
    return all(checks)


def validate_splits():
    """Validate train/val/test splits"""
    print("\n" + "="*65)
    print("  🔍 SPLIT VALIDATION")
    print("="*65)
    
    files = {
        'train': 'data/processed/train.pkl',
        'val': 'data/processed/val.pkl',
        'test': 'data/processed/test.pkl'
    }
    
    expected_sizes = {'train': 8000, 'val': 1000, 'test': 1000}
    checks = []
    
    for name, path in files.items():
        if not os.path.exists(path):
            print(f"  ❌ {path} not found")
            checks.append(False)
            continue
        
        df = pd.read_pickle(path)
        expected = expected_sizes[name]
        ok = len(df) == expected
        checks.append(ok)
        print(f"  {'✅' if ok else '❌'} {name}: {len(df)} samples (expected {expected})")
    
    return all(checks)


def main():
    raw_ok = validate_raw()
    bio_ok = validate_bio()
    split_ok = validate_splits()
    
    print("\n" + "="*65)
    print("  🎯 FINAL VERDICT")
    print("="*65)
    
    if raw_ok and bio_ok and split_ok:
        print("  ✅ ALL VALIDATIONS PASSED")
        print("  ➡️  Ready for model training")
    else:
        failed = []
        if not raw_ok: failed.append("RAW")
        if not bio_ok: failed.append("BIO")
        if not split_ok: failed.append("SPLITS")
        print(f"  ❌ Failed: {', '.join(failed)}")
    print("="*65)


if __name__ == "__main__":
    main()