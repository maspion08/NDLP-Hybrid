"""
Gazetteer Builder untuk Hybrid CRF v2
Tugas Akhir: Arga Ariyuda Avian (2221101774)

LANDASAN ILMIAH:
================
Huang et al. (2015) "BiLSTM-CRF for Sequence Tagging" membuktikan:
"In the BiLSTM-CRF model... gazetteer features boost tagging accuracy"

Srihari (2000) - Hybrid NER Strategy:
"MaxEnt is used in conjunction with features enriched by external gazetteers"

Tjong Kim Sang & De Meulder (2003) CoNLL-2003:
Top systems pakai gazetteer untuk NER (Person, Location, Organization)

TUJUAN:
=======
Build dictionary lookup dari training data untuk 3 entitas:
1. JABATAN dictionary (kata jabatan)
2. LOKASI dictionary (kota, provinsi)
3. NAMA prefix dictionary (nama Indonesia umum)
4. NIK label dictionary (kata kunci NIK)
5. PHONE label dictionary (kata kunci telepon)
6. Negative context keywords (Order ID, Invoice, dll)
"""
import os
import json
import pandas as pd
from collections import Counter

print("="*70)
print("  📚 GAZETTEER BUILDER for Hybrid CRF v2")
print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
print("="*70)

# Load training data
print("\n📂 Loading training data...")
df_train = pd.read_pickle('data/processed/train.pkl')
print(f"   Train samples: {len(df_train)}")

# ============================================================
# 1. JABATAN GAZETTEER
# ============================================================
print("\n🔍 Building JABATAN gazetteer...")

jabatan_tokens = Counter()
jabatan_phrases = Counter()

for tokens, labels in zip(df_train['tokens'], df_train['labels']):
    # Single-token JABATAN
    for tok, lab in zip(tokens, labels):
        if lab in ['B-JABATAN', 'I-JABATAN']:
            jabatan_tokens[tok.lower()] += 1
    
    # Multi-token JABATAN phrases
    phrase = []
    for tok, lab in zip(tokens, labels):
        if lab == 'B-JABATAN':
            if phrase:
                if len(phrase) >= 2:
                    jabatan_phrases[' '.join(phrase)] += 1
            phrase = [tok.lower()]
        elif lab == 'I-JABATAN':
            phrase.append(tok.lower())
        else:
            if phrase and len(phrase) >= 2:
                jabatan_phrases[' '.join(phrase)] += 1
            phrase = []
    if phrase and len(phrase) >= 2:
        jabatan_phrases[' '.join(phrase)] += 1

# Filter: minimum 2 occurrences (untuk avoid noise)
jabatan_dict = {tok for tok, count in jabatan_tokens.items() if count >= 2}
jabatan_phrases_dict = {phr for phr, count in jabatan_phrases.items() if count >= 2}

# JABATAN prefix keywords (untuk multi-token detection)
jabatan_prefix = {
    'kepala', 'wakil', 'asisten', 'sekretaris', 'kepala bagian',
    'kepala dinas', 'kepala bidang', 'direktur'
}

print(f"   Unique JABATAN tokens: {len(jabatan_dict)}")
print(f"   Unique JABATAN phrases: {len(jabatan_phrases_dict)}")
print(f"   Top 10 JABATAN tokens: {jabatan_tokens.most_common(10)}")

# ============================================================
# 2. LOKASI GAZETTEER
# ============================================================
print("\n🔍 Building LOKASI gazetteer...")

lokasi_tokens = Counter()
lokasi_phrases = Counter()

for tokens, labels in zip(df_train['tokens'], df_train['labels']):
    for tok, lab in zip(tokens, labels):
        if lab in ['B-LOKASI', 'I-LOKASI']:
            lokasi_tokens[tok.lower()] += 1
    
    phrase = []
    for tok, lab in zip(tokens, labels):
        if lab == 'B-LOKASI':
            if phrase and len(phrase) >= 2:
                lokasi_phrases[' '.join(phrase)] += 1
            phrase = [tok.lower()]
        elif lab == 'I-LOKASI':
            phrase.append(tok.lower())
        else:
            if phrase and len(phrase) >= 2:
                lokasi_phrases[' '.join(phrase)] += 1
            phrase = []
    if phrase and len(phrase) >= 2:
        lokasi_phrases[' '.join(phrase)] += 1

lokasi_dict = {tok for tok, count in lokasi_tokens.items() if count >= 2}
lokasi_phrases_dict = {phr for phr, count in lokasi_phrases.items() if count >= 2}

print(f"   Unique LOKASI tokens: {len(lokasi_dict)}")
print(f"   Unique LOKASI phrases: {len(lokasi_phrases_dict)}")
print(f"   Top 10 LOKASI tokens: {lokasi_tokens.most_common(10)}")

# ============================================================
# 3. NAMA Prefix Dictionary
# ============================================================
print("\n🔍 Building NAMA prefix dictionary...")

nama_first_tokens = Counter()  # Token pertama nama

for tokens, labels in zip(df_train['tokens'], df_train['labels']):
    for tok, lab in zip(tokens, labels):
        if lab == 'B-NAMA':
            # Hanya alphabet, capitalize (typical Indonesian names)
            if tok.isalpha() and len(tok) >= 2 and tok[0].isupper():
                nama_first_tokens[tok.lower()] += 1

# Use top 500 most common Indonesian first names
nama_dict = {tok for tok, count in nama_first_tokens.most_common(500)}

print(f"   Unique NAMA prefixes (top 500): {len(nama_dict)}")
print(f"   Top 10 NAMA: {nama_first_tokens.most_common(10)}")

# ============================================================
# 4. NIK Label Keywords (kata yang menandakan NIK akan muncul)
# ============================================================
print("\n🔍 Building NIK label keywords...")

# Predefined NIK label keywords (manual + akan augment dari data)
nik_labels = {
    'nik', 'NIK', 'Nik',
    'nomor_induk', 'nomor', 'induk',
    'no.nik', 'no_nik', 'id', 'ID',
    'identity', 'identification',
    'identity_number', 'identitynumber',
    'idnumber', 'id_number',
    'kependudukan', 'ktp',
    'no_ktp', 'noktp'
}

# Augment dengan token yang muncul SEBELUM B-NIK di training
for tokens, labels in zip(df_train['tokens'], df_train['labels']):
    for i, (tok, lab) in enumerate(zip(tokens, labels)):
        if lab == 'B-NIK' and i > 0:
            prev_tok = tokens[i-1].lower()
            # Skip punctuation
            if prev_tok in [':', '=', '"', "'", '|', ',']:
                if i > 1:
                    prev_tok = tokens[i-2].lower()
            nik_labels.add(prev_tok)

# Filter out non-alphanumeric
nik_labels = {l for l in nik_labels if any(c.isalpha() for c in l)}
print(f"   NIK label keywords: {len(nik_labels)}")
print(f"   Examples: {list(nik_labels)[:15]}")

# ============================================================
# 5. PHONE Label Keywords
# ============================================================
print("\n🔍 Building PHONE label keywords...")

phone_labels = {
    'hp', 'HP', 'Hp',
    'telepon', 'telp', 'tlp', 'tel',
    'phone', 'mobile', 'mobil', 'cellular',
    'kontak', 'contact',
    'nomor_telepon', 'nomortelepon',
    'phone_number', 'phonenumber',
    'no_hp', 'nohp'
}

for tokens, labels in zip(df_train['tokens'], df_train['labels']):
    for i, (tok, lab) in enumerate(zip(tokens, labels)):
        if lab == 'B-PHONE' and i > 0:
            prev_tok = tokens[i-1].lower()
            if prev_tok in [':', '=', '"', "'", '|', ',']:
                if i > 1:
                    prev_tok = tokens[i-2].lower()
            phone_labels.add(prev_tok)

phone_labels = {l for l in phone_labels if any(c.isalpha() for c in l)}
print(f"   PHONE label keywords: {len(phone_labels)}")
print(f"   Examples: {list(phone_labels)[:15]}")

# ============================================================
# 6. NEGATIVE CONTEXT KEYWORDS (KEY INNOVATION!)
# ============================================================
print("\n🔍 Building NEGATIVE context keywords...")
print("   (Keywords yang mengindikasikan BUKAN PII)")

# Predefined negative keywords - akan menjadi KILLER FEATURE
negative_keywords = {
    # Transaction-related
    'order', 'invoice', 'tracking', 'receipt',
    'reference', 'ref', 'transaction', 'transaksi',
    'booking', 'reservation', 'reservasi',
    
    # Code/ID
    'code', 'kode', 'serial', 'session', 'sesi',
    'auth', 'token', 'hash', 'hashcode',
    'uuid', 'guid', 'log',
    
    # Product/Inventory
    'product', 'produk', 'item', 'sku',
    'resi', 'nomor_resi', 'shipping',
    
    # Financial (non-NIK)
    'amount', 'jumlah', 'total', 'saldo',
    'rekening', 'account', 'bank',
    'tagihan', 'biaya', 'harga',
    
    # Tech
    'server', 'service', 'request',
    'api_key', 'apikey', 'key', 'kunci',
}

print(f"   Negative context keywords: {len(negative_keywords)}")
print(f"   Examples: {sorted(negative_keywords)[:15]}")

# ============================================================
# SAVE GAZETTEER
# ============================================================
print("\n💾 Saving gazetteer...")

gazetteer = {
    'jabatan_tokens': sorted(jabatan_dict),
    'jabatan_phrases': sorted(jabatan_phrases_dict),
    'jabatan_prefix': sorted(jabatan_prefix),
    'lokasi_tokens': sorted(lokasi_dict),
    'lokasi_phrases': sorted(lokasi_phrases_dict),
    'nama_prefixes': sorted(nama_dict),
    'nik_labels': sorted(nik_labels),
    'phone_labels': sorted(phone_labels),
    'negative_keywords': sorted(negative_keywords),
}

os.makedirs('data/gazetteer', exist_ok=True)
with open('data/gazetteer/gazetteer.json', 'w', encoding='utf-8') as f:
    json.dump(gazetteer, f, ensure_ascii=False, indent=2)

# Statistics
print("\n" + "="*70)
print("  📊 GAZETTEER STATISTICS")
print("="*70)
print(f"  JABATAN tokens     : {len(gazetteer['jabatan_tokens']):>6}")
print(f"  JABATAN phrases    : {len(gazetteer['jabatan_phrases']):>6}")
print(f"  JABATAN prefixes   : {len(gazetteer['jabatan_prefix']):>6}")
print(f"  LOKASI tokens      : {len(gazetteer['lokasi_tokens']):>6}")
print(f"  LOKASI phrases     : {len(gazetteer['lokasi_phrases']):>6}")
print(f"  NAMA prefixes      : {len(gazetteer['nama_prefixes']):>6}")
print(f"  NIK labels         : {len(gazetteer['nik_labels']):>6}")
print(f"  PHONE labels       : {len(gazetteer['phone_labels']):>6}")
print(f"  Negative keywords  : {len(gazetteer['negative_keywords']):>6}")
print()
print(f"  ✅ Saved: data/gazetteer/gazetteer.json")
print("="*70)