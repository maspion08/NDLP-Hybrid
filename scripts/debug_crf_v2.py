"""
Debug v2: Investigate kenapa CRF masih F1=1.0 setelah enrichment
"""
import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from importlib import import_module
features_module = import_module('07_features')

# Load model & data
print("="*70)
print("  🔬 DEBUG CRF v2: Why F1=1.0 after enrichment?")
print("="*70)

with open('models/crf_pure.pkl', 'rb') as f:
    crf = pickle.load(f)

df_test = pd.read_pickle('data/processed/test.pkl')

# === Check 1: Apakah test set mengandung adversarial? ===
print(f"\n📊 TEST 1: Adversarial samples di test set?")
print("-"*70)

if 'source' in df_test.columns:
    src_dist = df_test['source'].value_counts()
    print(f"   Test source distribution:")
    for src, count in src_dist.items():
        print(f"      {src}: {count}")
    
    adv_count = src_dist.get('adversarial', 0)
    if adv_count == 0:
        print(f"\n   ❌ MASALAH: Tidak ada adversarial samples di test set!")
    else:
        print(f"\n   ✅ Ada {adv_count} adversarial samples di test set")
else:
    print(f"   ⚠️  Column 'source' tidak ada di test set")

# === Check 2: Format distribution ===
print(f"\n📊 TEST 2: Format distribution di test set")
print("-"*70)
fmt_dist = df_test['format'].value_counts()
for fmt, count in fmt_dist.items():
    print(f"   {fmt}: {count}")

# === Check 3: Predict adversarial samples specifically ===
print(f"\n📊 TEST 3: Apakah CRF benar di adversarial samples?")
print("-"*70)

if 'source' in df_test.columns:
    adv_test = df_test[df_test['source'] == 'adversarial']
    
    if len(adv_test) > 0:
        X_adv, y_adv = features_module.dataset_to_features(
            adv_test, use_regex_features=False, verbose=False
        )
        y_pred_adv = crf.predict(X_adv)
        tokens_adv = adv_test['tokens'].tolist()
        
        # Hitung berapa yang salah di adversarial
        correct = 0
        wrong_examples = []
        
        for i, (true_seq, pred_seq, tokens) in enumerate(zip(y_adv, y_pred_adv, tokens_adv)):
            if true_seq == pred_seq:
                correct += 1
            else:
                if len(wrong_examples) < 5:
                    # Find difference
                    diffs = []
                    for j, (t, p, tok) in enumerate(zip(true_seq, pred_seq, tokens)):
                        if t != p:
                            diffs.append((tok, t, p))
                    wrong_examples.append({
                        'idx': i,
                        'payload': adv_test.iloc[i]['payload'][:100],
                        'diffs': diffs[:3]
                    })
        
        print(f"   Adversarial test samples: {len(adv_test)}")
        print(f"   Correct predictions: {correct}/{len(adv_test)} ({correct/len(adv_test)*100:.1f}%)")
        
        if wrong_examples:
            print(f"\n   ⚠️  {len(adv_test) - correct} salah, contoh:")
            for ex in wrong_examples[:3]:
                print(f"\n   [Sample #{ex['idx']}]")
                print(f"   Payload: {ex['payload']}...")
                for tok, true_lab, pred_lab in ex['diffs']:
                    print(f"      '{tok}': true={true_lab}, pred={pred_lab}")

# === Check 4: Manual stress test cases ===
print(f"\n📊 TEST 4: Stress test edge cases")
print("-"*70)

stress_cases = [
    {
        'desc': '16-digit Order ID (NOT NIK)',
        'tokens': ['Order', 'ID', ':', '1234567890123456', 'sudah', 'diproses'],
        'expected_no_pii': ['1234567890123456']  # should NOT be tagged as NIK
    },
    {
        'desc': 'Nomor invoice 16-digit',
        'tokens': ['Nomor', 'invoice', '9876543210987654', 'telah', 'dibayar'],
        'expected_no_pii': ['9876543210987654']
    },
    {
        'desc': 'Tracking number',
        'tokens': ['Tracking', 'number', ':', '5555444433332222', 'sedang', 'dalam', 'perjalanan'],
        'expected_no_pii': ['5555444433332222']
    },
    {
        'desc': 'NIK in proper context (should detect)',
        'tokens': ['NIK', 'milik', 'saya', 'adalah', '3271234567890123'],
        'expected_pii': [('3271234567890123', 'B-NIK')]
    },
]

for case in stress_cases:
    features = features_module.sentence_to_features(case['tokens'], use_regex_features=False)
    pred = crf.predict([features])[0]
    
    print(f"\n   [{case['desc']}]")
    print(f"   Input: {' '.join(case['tokens'])}")
    print(f"   Predicted:")
    for tok, lab in zip(case['tokens'], pred):
        if lab != 'O':
            print(f"      '{tok}' -> {lab}")
    
    # Check expectation
    if 'expected_no_pii' in case:
        for token in case['expected_no_pii']:
            if token in case['tokens']:
                idx = case['tokens'].index(token)
                if pred[idx].startswith('B-') or pred[idx].startswith('I-'):
                    print(f"      ❌ FALSE POSITIVE: '{token}' tagged as {pred[idx]}")
                else:
                    print(f"      ✅ Correctly not tagged as PII")
    
    if 'expected_pii' in case:
        for expected_tok, expected_lab in case['expected_pii']:
            idx = case['tokens'].index(expected_tok)
            if pred[idx] == expected_lab:
                print(f"      ✅ Correctly tagged: '{expected_tok}' -> {expected_lab}")
            else:
                print(f"      ❌ Expected {expected_lab}, got {pred[idx]}")

# === Check 5: Coverage analysis ===
print(f"\n📊 TEST 5: Apakah ada novel tokens di test?")
print("-"*70)

# Get vocabulary dari training feature
df_train = pd.read_pickle('data/processed/train.pkl')

train_tokens = set()
for tokens in df_train['tokens']:
    train_tokens.update(t.lower() for t in tokens)

test_tokens = set()
for tokens in df_test['tokens']:
    test_tokens.update(t.lower() for t in tokens)

novel = test_tokens - train_tokens
overlap = len(test_tokens & train_tokens)
print(f"   Train vocabulary: {len(train_tokens):,}")
print(f"   Test vocabulary: {len(test_tokens):,}")
print(f"   Overlap: {overlap:,} ({overlap/len(test_tokens)*100:.1f}%)")
print(f"   Novel in test: {len(novel):,}")

print(f"\n" + "="*70)
print(f"  📝 KESIMPULAN")
print(f"="*70)
print(f"""
  Jika CRF salah di adversarial samples atau stress test:
  → CRF tidak overfit, F1=1.0 valid untuk distribution yang sama
  
  Jika CRF benar di SEMUA adversarial samples:
  → Dataset adversarial tidak cukup challenging
  → Atau: word shape feature terlalu powerful
""")