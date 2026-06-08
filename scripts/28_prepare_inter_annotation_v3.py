"""
Prepare Inter-Annotator Data - FINAL VERSION
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Strategi: 
- Pakai 200 sampel dari Round 1 Anda (sudah completed)
- Generate CSV kosong untuk Rekan, sampel SAMA
- Anotasi Anda → tinggal export dari Round 1 (sudah ada)
"""
import os
import json
import pandas as pd

print("="*70)
print("  📋 PREPARE INTER-ANNOTATOR DATA (Final)")
print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
print("="*70)

# ============================================================
# Load Anotasi Anda (Round 1)
# ============================================================
print("\n📂 Loading Round 1 (anotasi Anda)...")
with open('evaluation/annotations_round1.json', 'r', encoding='utf-8') as f:
    round1_data = json.load(f)

print(f"   Round: {round1_data.get('round')}")
print(f"   Completed: {round1_data.get('completed')}")
print(f"   Total annotations: {len(round1_data['annotations'])}")

# ============================================================
# Load Held-Out untuk dapatkan raw_text (kalau tidak ada di annotations)
# ============================================================
print("\n📂 Loading held-out untuk raw_text reference...")
df_holdout = pd.read_pickle('data/test_holdout/naturalistic_bio.pkl')
print(f"   Holdout samples: {len(df_holdout)}")

# Build sample_id → raw_text mapping
# sample_id di Round 1 ADALAH index di holdout (kemungkinan)
holdout_dict = {}
for idx, row in df_holdout.iterrows():
    tokens = row.get('tokens', [])
    payload = row.get('payload', '')
    
    if payload:
        raw_text = payload
    elif isinstance(tokens, list) and tokens:
        raw_text = ' '.join(tokens)
    else:
        raw_text = ''
    
    holdout_dict[idx] = {
        'raw_text': raw_text,
        'format': row.get('format', 'unknown')
    }

# ============================================================
# Build CSV untuk Anotator B (Rekan)
# ============================================================
print("\n📝 Building CSV for Annotator B (Rekan)...")

annotator_b_rows = []
arga_rows = []  # Anotasi Anda dalam format yang sama

for ann in round1_data['annotations']:
    sample_id = ann['sample_id']
    
    # Get raw_text dari holdout
    if sample_id in holdout_dict:
        raw_text = holdout_dict[sample_id]['raw_text']
        format_type = holdout_dict[sample_id]['format']
    else:
        raw_text = ''
        format_type = ann.get('format', 'unknown')
    
    # Untuk Rekan: kosong, dia akan isi sendiri
    annotator_b_rows.append({
        'ID': f"sample_{sample_id:03d}",
        'Format': format_type,
        'Raw_Text': raw_text,
        'NIK': '',
        'PHONE': '',
        'NAMA': '',
        'JABATAN': '',
        'LOKASI': '',
        'Catatan': '',
    })
    
    # Untuk Anda: pakai anotasi Round 1
    arga_rows.append({
        'ID': f"sample_{sample_id:03d}",
        'Format': format_type,
        'Raw_Text': raw_text,
        'NIK': ' || '.join(ann.get('NIK', [])),
        'PHONE': ' || '.join(ann.get('PHONE', [])),
        'NAMA': ' || '.join(ann.get('NAMA', [])),
        'JABATAN': ' || '.join(ann.get('JABATAN', [])),
        'LOKASI': ' || '.join(ann.get('LOKASI', [])),
        'Catatan': ann.get('note', ''),
    })

# ============================================================
# Save CSV
# ============================================================
os.makedirs('evaluation', exist_ok=True)

# Untuk Rekan (kosong, akan diisi)
path_b = 'evaluation/sheet_for_annotator_b.csv'
pd.DataFrame(annotator_b_rows).to_csv(path_b, index=False, encoding='utf-8-sig')
print(f"   ✅ {path_b}")

# Untuk Anda (sudah terisi)
path_a = 'evaluation/sheet_arga_completed.csv'
pd.DataFrame(arga_rows).to_csv(path_a, index=False, encoding='utf-8-sig')
print(f"   ✅ {path_a}")

# Stats anotasi Anda
print("\n📊 Distribusi anotasi Anda (Round 1):")
total_nik = sum(len(ann.get('NIK', [])) for ann in round1_data['annotations'])
total_phone = sum(len(ann.get('PHONE', [])) for ann in round1_data['annotations'])
total_nama = sum(len(ann.get('NAMA', [])) for ann in round1_data['annotations'])
total_jabatan = sum(len(ann.get('JABATAN', [])) for ann in round1_data['annotations'])
total_lokasi = sum(len(ann.get('LOKASI', [])) for ann in round1_data['annotations'])

print(f"   NIK     : {total_nik} entitas")
print(f"   PHONE   : {total_phone} entitas")
print(f"   NAMA    : {total_nama} entitas")
print(f"   JABATAN : {total_jabatan} entitas")
print(f"   LOKASI  : {total_lokasi} entitas")
print(f"   TOTAL   : {total_nik+total_phone+total_nama+total_jabatan+total_lokasi} entitas")

print("\n" + "="*70)
print("  📊 SUMMARY")
print("="*70)
print(f"  Total samples       : {len(annotator_b_rows)}")
print(f"  Anotasi Anda        : ✅ Sudah terisi dari Round 1")
print(f"  Anotasi Rekan       : ⏳ Menunggu (sheet kosong sudah siap)")
print()
print(f"  📌 File untuk REKAN: {path_b}")
print(f"  📌 File anotasi Anda: {path_a}")
print("="*70)

print("\n📝 LANGKAH SELANJUTNYA:")
print("  1. Buka https://sheets.google.com")
print(f"  2. Import: {path_b}")
print("  3. Setting saat import:")
print("     • Separator: Comma")
print("     • Convert text to numbers: NO (PENTING untuk NIK!)")
print("  4. Format kolom NIK sebagai TEXT:")
print("     • Select kolom NIK → Format → Number → Plain text")
print("  5. Share sheet ke rekan: 'Anyone with link can edit'")
print("  6. Kirim link + annotation guideline ke rekan")
print()
print("  💡 Strategi: Rekan anotasi 200 sampel SAMA dengan Anda")
print("              Setelah selesai, compare untuk Cohen's Kappa")