"""
Debug script untuk verify hipotesis kenapa HMM gagal di NIK/PHONE
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import pickle
from collections import Counter

# Load data
df_train = pd.read_pickle('data/processed/train.pkl')
df_test = pd.read_pickle('data/processed/test.pkl')

print("="*70)
print("  🔬 DEBUG: Why HMM Fail on NIK & PHONE?")
print("="*70)

# === Hipotesis 1: NIK/PHONE tokens hampir tidak overlap antara train & test ===
print("\n📊 HIPOTESIS: Token Overlap Train vs Test")
print("-"*70)

for entity in ['NIK', 'PHONE', 'NAMA', 'JABATAN', 'LOKASI']:
    # Collect tokens dari train yang berlabel B-{entity}
    train_tokens = set()
    for _, row in df_train.iterrows():
        for tok, lab in zip(row['tokens'], row['labels']):
            if lab == f'B-{entity}':
                train_tokens.add(tok.lower())
    
    # Same untuk test
    test_tokens = set()
    for _, row in df_test.iterrows():
        for tok, lab in zip(row['tokens'], row['labels']):
            if lab == f'B-{entity}':
                test_tokens.add(tok.lower())
    
    overlap = train_tokens & test_tokens
    overlap_pct = len(overlap) / len(test_tokens) * 100 if test_tokens else 0
    
    print(f"\n  {entity:<8}: {len(train_tokens):>6} train tokens, {len(test_tokens):>6} test tokens")
    print(f"           {len(overlap):>6} overlap ({overlap_pct:.1f}%)")
    
    if overlap_pct < 10:
        print(f"           ❌ Almost no overlap → HMM tidak bisa belajar")
    elif overlap_pct < 50:
        print(f"           ⚠️  Low overlap")
    else:
        print(f"           ✅ Good overlap → HMM bisa belajar")

# === Hipotesis 2: Cek prediksi HMM untuk NIK/PHONE di test ===
print("\n\n📊 SAMPLE PREDICTION untuk NIK & PHONE")
print("-"*70)

# Load HMM model
sys.path.insert(0, 'scripts')
from importlib import import_module
hmm_module = import_module('11_train_hmm')
CategoricalHMM = hmm_module.CategoricalHMM

model = CategoricalHMM.load('models/hmm_pure.pkl')

# Test 5 sampel
for i in range(3):
    row = df_test.iloc[i]
    tokens = row['tokens']
    true_labels = row['labels']
    pred_labels = model.viterbi_decode(tokens)
    
    print(f"\n  Sample {i+1}:")
    print(f"  Format: {row['format']}")
    
    # Tampilkan token NIK
    for tok, true_lab, pred_lab in zip(tokens, true_labels, pred_labels):
        if true_lab in ['B-NIK', 'B-PHONE'] or pred_lab in ['B-NIK', 'B-PHONE']:
            in_vocab = tok.lower() in model.token_to_idx
            print(f"    Token: '{tok}' | True: {true_lab:<10} Pred: {pred_lab:<10} | In vocab: {in_vocab}")

print("\n" + "="*70)
print("  📝 KESIMPULAN")
print("="*70)
print("""
  Jika overlap NIK/PHONE rendah (<10%), itu artinya:
  - HMM tidak pernah lihat NIK/PHONE di test selama training
  - Token masuk <UNK>
  - HMM tidak bisa generalize → predict 'O'
  
  → SOLUSI: Hybrid HMM dengan Regex-as-a-Feature akan FIX ini!
""")