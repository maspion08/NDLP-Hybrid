"""
Prepare Inter-Annotator Agreement Data (Simplified Version)
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Strategi: 
- Ambil 200 sampel dari held-out pickle (source of truth)
- Generate CSV kosong untuk Anda DAN rekan
- Kedua orang anotasi paralel, BARU bandingkan

Keuntungan:
- Tidak tergantung format annotations_round1.json yang mungkin aneh
- Anda dan rekan punya starting point yang sama
- Methodology paling bersih untuk inter-annotator
"""
import os
import json
import pandas as pd

print("="*70)
print("  📋 PREPARE INTER-ANNOTATOR DATA (Simplified)")
print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
print("="*70)

# ============================================================
# Load Held-Out Pickle (source of truth)
# ============================================================
holdout_path = 'data/test_holdout/naturalistic_bio.pkl'
print(f"\n📂 Loading held-out test set...")

if not os.path.exists(holdout_path):
    print(f"   ❌ File tidak ditemukan: {holdout_path}")
    exit(1)

df_holdout = pd.read_pickle(holdout_path)
print(f"   ✅ Loaded: {len(df_holdout)} samples")
print(f"   Columns: {list(df_holdout.columns)}")

# ============================================================
# Stratified Sampling: 200 samples
# ============================================================
print("\n🎯 Stratified sampling 200 samples...")

# Cek apakah ada kolom 'format'
if 'format' in df_holdout.columns:
    formats = df_holdout['format'].value_counts()
    print(f"   Formats: {dict(formats)}")
    
    # Distribute 200 across formats proportionally
    total = len(df_holdout)
    samples_per_format = {}
    for fmt, count in formats.items():
        n = round(200 * count / total)
        samples_per_format[fmt] = max(n, 1)
    
    # Adjust total to 200
    diff = 200 - sum(samples_per_format.values())
    if diff != 0:
        largest_fmt = max(samples_per_format, key=samples_per_format.get)
        samples_per_format[largest_fmt] += diff
    
    print(f"   Distribution: {samples_per_format}")
    
    df_subset = pd.concat([
        df_holdout[df_holdout['format'] == fmt].sample(n, random_state=42)
        for fmt, n in samples_per_format.items()
    ]).reset_index(drop=True)
else:
    print(f"   No 'format' column, taking random 200 samples")
    df_subset = df_holdout.sample(200, random_state=42).reset_index(drop=True)

print(f"   ✅ Subset: {len(df_subset)} samples")

# ============================================================
# CREATE CSV untuk Annotator B (Rekan)
# ============================================================
print("\n📝 Creating CSV for Annotator B (Rekan)...")

annotator_rows = []
for idx, row in df_subset.iterrows():
    sample_id = f"sample_{idx+1:03d}"
    
    # Get raw_text (kalau ada) atau gabung tokens
    if 'raw_text' in row and row['raw_text']:
        raw_text = row['raw_text']
    elif 'text' in row and row['text']:
        raw_text = row['text']
    elif 'tokens' in row and isinstance(row['tokens'], list):
        raw_text = ' '.join(row['tokens'])
    else:
        raw_text = ''
    
    annotator_rows.append({
        'ID': sample_id,
        'Raw_Text': raw_text,
        'NIK': '',          # Annotator B akan isi
        'PHONE': '',
        'NAMA': '',
        'JABATAN': '',
        'LOKASI': '',
        'Catatan': '',      # Opsional notes
    })

# ============================================================
# CREATE CSV untuk Anda (Annotator A)
# ============================================================
print("📝 Creating CSV for Anda (Annotator A)...")

arga_rows = []
for idx, row in df_subset.iterrows():
    sample_id = f"sample_{idx+1:03d}"
    
    if 'raw_text' in row and row['raw_text']:
        raw_text = row['raw_text']
    elif 'text' in row and row['text']:
        raw_text = row['text']
    elif 'tokens' in row and isinstance(row['tokens'], list):
        raw_text = ' '.join(row['tokens'])
    else:
        raw_text = ''
    
    arga_rows.append({
        'ID': sample_id,
        'Raw_Text': raw_text,
        'NIK': '',          # Anda akan isi
        'PHONE': '',
        'NAMA': '',
        'JABATAN': '',
        'LOKASI': '',
        'Catatan': '',
    })

# ============================================================
# CREATE GROUND TRUTH CSV (auto-extract dari BIO labels)
# ============================================================
print("📝 Creating ground truth CSV (untuk validation nanti)...")

def extract_entities_from_bio(tokens, labels):
    """Extract entities dari BIO labels"""
    entities = {'NIK': [], 'PHONE': [], 'NAMA': [], 'JABATAN': [], 'LOKASI': []}
    current_entity = None
    current_tokens = []
    
    for tok, lab in zip(tokens, labels):
        if lab.startswith('B-'):
            if current_entity:
                entities[current_entity].append(' '.join(current_tokens))
            current_entity = lab[2:]
            current_tokens = [tok]
        elif lab.startswith('I-') and current_entity == lab[2:]:
            current_tokens.append(tok)
        else:
            if current_entity:
                entities[current_entity].append(' '.join(current_tokens))
                current_entity = None
                current_tokens = []
    
    if current_entity:
        entities[current_entity].append(' '.join(current_tokens))
    
    return entities

ground_truth_rows = []
for idx, row in df_subset.iterrows():
    sample_id = f"sample_{idx+1:03d}"
    
    tokens = row.get('tokens', [])
    labels = row.get('labels', [])
    
    if isinstance(tokens, list) and isinstance(labels, list) and tokens and labels:
        entities = extract_entities_from_bio(tokens, labels)
    else:
        entities = {'NIK': [], 'PHONE': [], 'NAMA': [], 'JABATAN': [], 'LOKASI': []}
    
    if 'raw_text' in row and row['raw_text']:
        raw_text = row['raw_text']
    elif isinstance(tokens, list) and tokens:
        raw_text = ' '.join(tokens)
    else:
        raw_text = ''
    
    ground_truth_rows.append({
        'ID': sample_id,
        'Raw_Text': raw_text,
        'NIK': ' || '.join(entities['NIK']),
        'PHONE': ' || '.join(entities['PHONE']),
        'NAMA': ' || '.join(entities['NAMA']),
        'JABATAN': ' || '.join(entities['JABATAN']),
        'LOKASI': ' || '.join(entities['LOKASI']),
    })

# ============================================================
# SAVE ALL CSV
# ============================================================
os.makedirs('evaluation', exist_ok=True)

# Annotator B (Rekan)
path_b = 'evaluation/sheet_for_annotator_b.csv'
pd.DataFrame(annotator_rows).to_csv(path_b, index=False, encoding='utf-8-sig')
print(f"\n✅ {path_b}")

# Annotator A (Anda)
path_a = 'evaluation/sheet_for_arga.csv'
pd.DataFrame(arga_rows).to_csv(path_a, index=False, encoding='utf-8-sig')
print(f"✅ {path_a}")

# Ground Truth (untuk reference)
path_gt = 'evaluation/ground_truth_subset.csv'
pd.DataFrame(ground_truth_rows).to_csv(path_gt, index=False, encoding='utf-8-sig')
print(f"✅ {path_gt}")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "="*70)
print("  📊 SUMMARY")
print("="*70)
print(f"  Total samples       : {len(df_subset)}")
print()
print(f"  📌 File untuk REKAN (Annotator B):")
print(f"     {path_b}")
print()
print(f"  📌 File untuk ANDA (Annotator A):")
print(f"     {path_a}")
print()
print(f"  📌 Ground Truth (reference):")
print(f"     {path_gt}")
print("="*70)

print("\n📝 LANGKAH SELANJUTNYA:")
print("  1. Buka https://sheets.google.com")
print("  2. Buat 2 sheet baru:")
print("     a) 'Annotation - Annotator A (Arga)'")
print("     b) 'Annotation - Annotator B (Rekan)'")
print(f"  3. Import {path_a} ke sheet Anda")
print(f"  4. Import {path_b} ke sheet rekan")
print("  5. Format kolom NIK & PHONE sebagai TEXT (Format → Number → Plain text)")
print("  6. Share sheet rekan ke rekan dengan 'Anyone with link can edit'")
print("  7. Anda dan rekan anotasi PARALEL (tidak saling lihat)")
print("  8. Setelah selesai, jalankan: python scripts/29_compute_inter_kappa.py")
print()
print("  🎯 STRATEGI: Anda dan rekan kerja PARALEL untuk inter-annotator")
print("              agreement yang BERSIH (no contamination dari Round 1)")