"""
Prepare Inter-Annotator Agreement Data untuk Google Sheets (ROBUST VERSION)
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Script ini auto-detect struktur JSON annotations_round1.json
dan handle berbagai format yang mungkin ada.
"""
import os
import json
import pandas as pd
import pickle

print("="*70)
print("  📋 PREPARE INTER-ANNOTATOR DATA (Robust Version)")
print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
print("="*70)

# ============================================================
# LOAD DATA - Try multiple sources
# ============================================================
samples = []

# Try 1: annotations_round1.json
annotations_path = 'evaluation/annotations_round1.json'
if os.path.exists(annotations_path):
    print(f"\n📂 Trying: {annotations_path}")
    with open(annotations_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    print(f"   Type: {type(raw_data).__name__}")
    
    # Handle different structures
    if isinstance(raw_data, dict):
        # Case A: {'sample_id': {tokens, labels, ...}}
        if all(isinstance(v, dict) for v in raw_data.values()):
            print(f"   Detected: dict of dicts (keyed by sample ID)")
            for sid, sample in raw_data.items():
                samples.append({
                    'id': sid,
                    'raw_text': sample.get('raw_text', sample.get('text', ' '.join(sample.get('tokens', [])))),
                    'tokens': sample.get('tokens', []),
                    'labels': sample.get('labels', sample.get('annotations', []))
                })
        
        # Case B: {'annotations': [...], 'metadata': {...}}
        elif 'annotations' in raw_data or 'samples' in raw_data or 'data' in raw_data:
            key = 'annotations' if 'annotations' in raw_data else ('samples' if 'samples' in raw_data else 'data')
            print(f"   Detected: dict with '{key}' field")
            for idx, sample in enumerate(raw_data[key]):
                samples.append({
                    'id': sample.get('id', f"sample_{idx:03d}"),
                    'raw_text': sample.get('raw_text', sample.get('text', '')),
                    'tokens': sample.get('tokens', []),
                    'labels': sample.get('labels', sample.get('annotations', []))
                })
        else:
            print(f"   ⚠️ Unknown dict structure. Keys: {list(raw_data.keys())[:5]}")
    
    elif isinstance(raw_data, list):
        # Case C: list of dicts
        if raw_data and isinstance(raw_data[0], dict):
            print(f"   Detected: list of dicts")
            for idx, sample in enumerate(raw_data):
                samples.append({
                    'id': sample.get('id', f"sample_{idx:03d}"),
                    'raw_text': sample.get('raw_text', sample.get('text', '')),
                    'tokens': sample.get('tokens', []),
                    'labels': sample.get('labels', sample.get('annotations', []))
                })
        # Case D: list of strings (kemungkinan ID atau text saja)
        elif raw_data and isinstance(raw_data[0], str):
            print(f"   ⚠️ Detected: list of strings - tidak bisa diproses")
            print(f"   First 3 items: {raw_data[:3]}")

# Try 2: Fallback ke kappa subset dari holdout pickle
if len(samples) == 0 or len(samples) < 50:
    print(f"\n⚠️ Annotations file tidak ada/incomplete. Akan ambil dari holdout pickle.")
    
    holdout_path = 'data/test_holdout/naturalistic_bio.pkl'
    kappa_subset_path = 'evaluation/kappa_subset_ids.json'
    
    if os.path.exists(holdout_path):
        df_holdout = pd.read_pickle(holdout_path)
        print(f"   Loaded holdout: {len(df_holdout)} samples")
        
        # If ada subset ID file, pakai itu
        if os.path.exists(kappa_subset_path):
            with open(kappa_subset_path, 'r') as f:
                subset_data = json.load(f)
            if isinstance(subset_data, list):
                subset_ids = subset_data
            elif isinstance(subset_data, dict) and 'ids' in subset_data:
                subset_ids = subset_data['ids']
            else:
                subset_ids = []
            
            print(f"   Subset IDs found: {len(subset_ids)}")
            df_subset = df_holdout[df_holdout.index.isin(subset_ids)] if subset_ids else df_holdout.head(200)
        else:
            # Stratified sample 200 dari holdout
            print(f"   No subset file. Taking stratified 200 samples...")
            if 'format' in df_holdout.columns:
                df_subset = df_holdout.groupby('format', group_keys=False).apply(
                    lambda x: x.sample(min(len(x), 200 // df_holdout['format'].nunique()), random_state=42)
                )
            else:
                df_subset = df_holdout.sample(200, random_state=42)
        
        samples = []
        for idx, row in df_subset.iterrows():
            tokens = row['tokens'] if isinstance(row['tokens'], list) else []
            labels = row['labels'] if isinstance(row['labels'], list) else []
            raw_text = row.get('raw_text', ' '.join(tokens))
            
            samples.append({
                'id': f"sample_{idx:03d}",
                'raw_text': raw_text,
                'tokens': tokens,
                'labels': labels
            })
        
        print(f"   ✅ Loaded {len(samples)} samples from holdout")

if len(samples) == 0:
    print("\n❌ ERROR: Tidak bisa load samples dari file manapun.")
    print("   File yang dicek:")
    print(f"   - {annotations_path}")
    print(f"   - data/test_holdout/naturalistic_bio.pkl")
    exit(1)

print(f"\n✅ Total samples loaded: {len(samples)}")

# Jika lebih dari 200, ambil 200 pertama
if len(samples) > 200:
    samples = samples[:200]
    print(f"   Trimmed to 200 samples")

# ============================================================
# CREATE GOOGLE SHEETS CSV (untuk Annotator B)
# ============================================================
print("\n📝 Creating Google Sheets CSV for Annotator B...")

annotator_rows = []
for idx, sample in enumerate(samples, 1):
    annotator_rows.append({
        'ID': sample['id'],
        'Raw_Text': sample['raw_text'],
        'NIK': '',          # Annotator B akan isi
        'PHONE': '',
        'NAMA': '',
        'JABATAN': '',
        'LOKASI': '',
        'Catatan': '',
    })

os.makedirs('evaluation', exist_ok=True)
output_path_annotator = 'evaluation/sheet_for_annotator_b.csv'
df_annotator = pd.DataFrame(annotator_rows)
df_annotator.to_csv(output_path_annotator, index=False, encoding='utf-8-sig')

print(f"   ✅ {output_path_annotator}")
print(f"   📊 Total rows: {len(annotator_rows)}")

# ============================================================
# CREATE YOUR ANNOTATIONS CSV (untuk perbandingan)
# ============================================================
print("\n📝 Creating your annotations CSV (untuk perbandingan)...")

arga_rows = []
for sample in samples:
    arga_rows.append({
        'ID': sample['id'],
        'Raw_Text': sample['raw_text'],
        'Tokens': ' | '.join(sample['tokens']) if sample['tokens'] else '',
        'Labels': ' | '.join(sample['labels']) if sample['labels'] else '',
    })

output_path_arga = 'evaluation/annotations_arga_export.csv'
df_arga = pd.DataFrame(arga_rows)
df_arga.to_csv(output_path_arga, index=False, encoding='utf-8-sig')

print(f"   ✅ {output_path_arga}")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "="*70)
print("  📊 SUMMARY")
print("="*70)
print(f"  Total samples       : {len(samples)}")
print(f"  Tokens not empty    : {sum(1 for s in samples if s['tokens'])}")
print(f"  Labels not empty    : {sum(1 for s in samples if s['labels'])}")
print()
print(f"  File untuk Annotator B (Google Sheets):")
print(f"     {output_path_annotator}")
print()
print(f"  File anotasi Anda (untuk perbandingan):")
print(f"     {output_path_arga}")
print("="*70)

print("\n📝 LANGKAH SELANJUTNYA:")
print("  1. Buka https://sheets.google.com")
print("  2. Klik 'Blank' untuk buat sheet baru")
print(f"  3. File → Import → Upload → pilih {output_path_annotator}")
print("  4. Settings: Separator = Comma, Convert text to numbers = NO")
print("  5. Klik 'Share' → 'Anyone with link can edit'")
print("  6. Copy link, kirim ke rekan annotator")
print("  7. Sertakan annotation guideline yang sudah disiapkan")
print()
print("  💡 TIP: Kolom NIK perlu di-format sebagai TEXT (Format → Number → Plain text)")
print("         supaya angka 16 digit tidak dikonversi ke notasi ilmiah")