"""
Debug & Stress Test untuk CRF Murni
Memverifikasi hasil F1=1.0 valid atau ada bias
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import pickle
from collections import Counter
from importlib import import_module

features_module = import_module('07_features')

# Load CRF model
with open('models/crf_pure.pkl', 'rb') as f:
    crf = pickle.load(f)

print("="*70)
print("  🔬 STRESS TEST CRF MURNI")
print("="*70)

# Test 1: Apakah CRF cuma memorize pattern atau benar-benar belajar?
print("\n📊 TEST 1: Edge Cases (Adversarial Examples)")
print("-"*70)

edge_cases = [
    # Test 1a: NIK dengan format mirip tapi bukan PII
    {
        'tokens': ['Order', 'ID', ':', '1234567890123456', 'sudah', 'diproses'],
        'expected': 'O for "1234567890123456" (16 digit but in non-PII context)',
        'description': 'False positive test: 16-digit number in order context'
    },
    # Test 1b: NIK dalam konteks yang tidak biasa
    {
        'tokens': ['NIK', 'milik', 'saya', 'adalah', '3271234567890123', '.'],
        'expected': 'B-NIK for "3271234567890123"',
        'description': 'NIK in narrative form'
    },
    # Test 1c: Phone dalam konteks ambigu  
    {
        'tokens': ['Saldo', ':', 'Rp', '5000000', 'Telepon', ':', '081234567890'],
        'expected': 'B-PHONE for "081234567890", O for "5000000"',
        'description': 'Phone vs amount disambiguation'
    },
    # Test 1d: Nama yang tidak ada di training
    {
        'tokens': ['Pegawai', 'baru', 'bernama', 'Xenophon', 'Yudistira', 'akan', 'bergabung'],
        'expected': 'B-NAMA for "Xenophon", I-NAMA for "Yudistira"',
        'description': 'Out-of-vocabulary names'
    },
    # Test 1e: Jabatan baru yang tidak di training set
    {
        'tokens': ['Saya', 'adalah', 'Manajer', 'Operasional', 'Senior', 'di', 'Surabaya'],
        'expected': 'JABATAN for "Manajer Operasional Senior" (not in train)',
        'description': 'Unknown job title'
    }
]

for i, case in enumerate(edge_cases, 1):
    tokens = case['tokens']
    features = features_module.sentence_to_features(tokens, use_regex_features=False)
    pred = crf.predict([features])[0]
    
    print(f"\n  [Test 1.{i}] {case['description']}")
    print(f"  Input    : {tokens}")
    print(f"  Expected : {case['expected']}")
    print(f"  Predicted: {list(zip(tokens, pred))}")

# Test 2: Cek apakah CRF benar-benar tidak overfit
print("\n\n📊 TEST 2: Detection di Format Baru")
print("-"*70)

novel_examples = [
    # Format baru yang tidak ada di training
    "URL: https://example.com/user?nik=3201234567890123&phone=081234567890",
    "<user><nik>1234567890123456</nik><name>Budi Santoso</name></user>",
    "INSERT INTO users VALUES ('3271234567890123', 'Andi Wijaya')"
]

for i, text in enumerate(novel_examples, 1):
    # Tokenize manually (simple)
    import re
    tokens = re.findall(r'\+62\d{8,12}|\d+|[a-zA-Z\u00C0-\u017F]+|[^\w\s]', text)
    features = features_module.sentence_to_features(tokens, use_regex_features=False)
    pred = crf.predict([features])[0]
    
    print(f"\n  [Test 2.{i}] {text}")
    print(f"  Tokens: {tokens[:15]}...")
    
    # Show only non-O predictions
    detections = [(t, l) for t, l in zip(tokens, pred) if l != 'O']
    if detections:
        print(f"  Detections:")
        for tok, lab in detections:
            print(f"     '{tok}' -> {lab}")
    else:
        print(f"  No PII detected")

# Test 3: Confusion analysis pada test set
print("\n\n📊 TEST 3: Detail Test Set Performance")
print("-"*70)

df_test = pd.read_pickle('data/processed/test.pkl')
X_test, y_test = features_module.dataset_to_features(df_test, use_regex_features=False, verbose=False)
y_pred = crf.predict(X_test)

# Hitung total predictions
all_true_labels = []
all_pred_labels = []
for true_seq, pred_seq in zip(y_test, y_pred):
    all_true_labels.extend(true_seq)
    all_pred_labels.extend(pred_seq)

# Confusion per token-level
print(f"\n  Total tokens evaluated: {len(all_true_labels):,}")

# Count per format
print("\n  📊 Per-format accuracy:")
for fmt in df_test['format'].unique():
    fmt_indices = df_test[df_test['format'] == fmt].index.tolist()
    correct = 0
    total = 0
    for idx in fmt_indices:
        # Find position in test set
        pos = df_test.index.get_loc(idx)
        true_seq = y_test[pos]
        pred_seq = y_pred[pos]
        for t, p in zip(true_seq, pred_seq):
            total += 1
            if t == p:
                correct += 1
    acc = correct / total * 100 if total > 0 else 0
    print(f"     {fmt:<12}: {correct}/{total} ({acc:.2f}%)")

print("\n" + "="*70)
print("  📝 KESIMPULAN")
print("="*70)
print("""
  Jika CRF berhasil di edge cases (Test 1) dan format baru (Test 2):
  → Hasil F1=1.0 VALID, CRF benar-benar belajar pattern
  
  Jika CRF gagal di edge cases:
  → Hasil F1=1.0 disebabkan overfitting ke training distribution
  → Solusi: tambah data augmentation atau test set yang lebih diverse
""")