"""
NERGrit Corpus Loader & Adapter (REVISED v2)
Tugas Akhir: Arga Ariyuda Avian (2221101774)

PERBAIKAN dari v1:
1. Fix BIO consistency saat inject NIK
2. Filter ketat untuk PER (hanya yang punya B-PER)
3. Skip GPE yang ambiguous (OJK, Dinas, dll)
4. Validasi tag setelah injeksi

Sumber Dataset:
- Nergrit Corpus by PT Gria Inovasi Teknologi (GRIT)
- URL: https://huggingface.co/datasets/grit-id/id_nergrit_corpus
"""
import os
import json
import random
import pandas as pd
from datasets import load_dataset
from tqdm import tqdm
from collections import Counter

# Reproducibility
SEED = 42
random.seed(SEED)


# Mapping NERGrit tags
NERGRIT_TAG_NAMES = {
    0: 'I-CRD', 1: 'B-CRD',
    2: 'I-DAT', 3: 'B-DAT',
    4: 'I-EVT', 5: 'B-EVT',
    6: 'I-FAC', 7: 'B-FAC',
    8: 'I-GPE', 9: 'B-GPE',
    10: 'I-LAW', 11: 'B-LAW',
    12: 'I-LOC', 13: 'B-LOC',
    14: 'I-MON', 15: 'B-MON',
    16: 'I-NOR', 17: 'B-NOR',
    18: 'I-ORD', 19: 'B-ORD',
    20: 'I-ORG', 21: 'B-ORG',
    22: 'I-PER', 23: 'B-PER',
    24: 'I-PRC', 25: 'B-PRC',
    26: 'I-PRD', 27: 'B-PRD',
    28: 'I-QTY', 29: 'B-QTY',
    30: 'I-REG', 31: 'B-REG',
    32: 'I-TIM', 33: 'B-TIM',
    34: 'I-WOA', 35: 'B-WOA',
    36: 'I-LAN', 37: 'B-LAN',
    38: 'O'
}

# Mapping ke PII labels
# REVISED: Hanya LOC (real location), bukan GPE (geopolitical bisa ambigu)
PII_MAPPING = {
    'B-PER': 'B-NAMA',    'I-PER': 'I-NAMA',
    'B-LOC': 'B-LOKASI',  'I-LOC': 'I-LOKASI',
    # GPE di-skip karena banyak ambigu (OJK, Dinas, etc)
}

# List kata yang sering false positive sebagai LOKASI
LOCATION_BLACKLIST = {
    'OJK', 'BPK', 'BUMN', 'PNS', 'TNI', 'POLRI', 'KPK',
    'Dinas', 'Departemen', 'Kementerian', 'Lembaga',
    'Bank', 'Perusahaan', 'PT', 'CV', 'UD'
}


class NERGritAdapterV2:
    """Improved adapter dengan BIO consistency fix"""
    
    def __init__(self):
        self.dataset = None
    
    def download_nergrit(self):
        """Download NERGrit corpus"""
        print("\n📥 Downloading NERGrit Corpus from Hugging Face...")
        print("   URL: https://huggingface.co/datasets/grit-id/id_nergrit_corpus")
        
        try:
            self.dataset = load_dataset("grit-id/id_nergrit_corpus", "ner")
            print(f"   ✅ Downloaded successfully")
            
            for split_name in self.dataset.keys():
                n = len(self.dataset[split_name])
                print(f"   - {split_name}: {n:,} samples")
            
            return True
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def convert_tags(self, tag_ids):
        """Convert numeric tags to string"""
        return [NERGRIT_TAG_NAMES.get(tag_id, 'O') for tag_id in tag_ids]
    
    def map_to_pii_labels(self, tokens, tags):
        """
        Map NERGrit tags → PII labels with blacklist filter.
        
        REVISED:
        - Filter token yang ada di LOCATION_BLACKLIST (tidak di-tag sebagai LOKASI)
        - Skip GPE (only use LOC)
        """
        pii_labels = []
        
        for token, tag in zip(tokens, tags):
            mapped = PII_MAPPING.get(tag, 'O')
            
            # Filter blacklisted tokens
            if mapped in ['B-LOKASI', 'I-LOKASI']:
                if token in LOCATION_BLACKLIST:
                    pii_labels.append('O')
                    continue
            
            pii_labels.append(mapped)
        
        return pii_labels
    
    def fix_bio_consistency(self, labels):
        """
        Fix BIO consistency: pastikan I-X selalu didahului B-X atau I-X yang sama.
        Jika I-X muncul tanpa B-X sebelumnya, ubah ke B-X.
        """
        fixed = []
        prev_entity = None
        
        for label in labels:
            if label.startswith('I-'):
                entity = label[2:]
                # Check apakah label sebelumnya match
                if prev_entity != entity:
                    # I- tidak punya B- sebelumnya, ubah jadi B-
                    fixed.append(f'B-{entity}')
                    prev_entity = entity
                else:
                    fixed.append(label)
                    prev_entity = entity
            elif label.startswith('B-'):
                fixed.append(label)
                prev_entity = label[2:]
            else:  # O
                fixed.append('O')
                prev_entity = None
        
        return fixed
    
    def has_complete_per_entity(self, tags):
        """Check apakah ada entity PER yang lengkap (B-PER + optional I-PER)"""
        i = 0
        while i < len(tags):
            if tags[i] == 'B-PER':
                return True
            i += 1
        return False
    
    def filter_relevant_sentences(self, n_target=500):
        """Filter sentences yang punya entity relevan"""
        print(f"\n🔍 Filtering sentences with PER (Person) entities...")
        
        all_sentences = []
        for split_name in self.dataset.keys():
            for sample in self.dataset[split_name]:
                tokens = sample['tokens']
                tag_ids = sample['ner_tags']
                tags = self.convert_tags(tag_ids)
                
                # REVISED: Strict filter, MUST have B-PER
                has_b_per = self.has_complete_per_entity(tags)
                has_loc = any(t == 'B-LOC' for t in tags)
                
                # Hanya yang punya B-PER (Person yang clear)
                if has_b_per:
                    all_sentences.append({
                        'tokens': tokens,
                        'tags': tags,
                        'has_per': has_b_per,
                        'has_loc': has_loc,
                        'token_count': len(tokens),
                    })
        
        print(f"   Total with B-PER: {len(all_sentences):,}")
        
        # Filter token range 5-50
        filtered = [s for s in all_sentences if 5 <= s['token_count'] <= 50]
        print(f"   After length filter (5-50 tokens): {len(filtered):,}")
        
        # Sort: prefer those with both PER and LOC
        filtered.sort(key=lambda x: (x['has_loc'], -x['token_count']), reverse=True)
        
        # Take top n_target
        if len(filtered) >= n_target:
            selected = filtered[:n_target]
        else:
            print(f"   ⚠️  Only {len(filtered)} matches, taking all")
            selected = filtered
        
        # Stats
        with_loc = sum(1 for s in selected if s['has_loc'])
        print(f"   Selected: {len(selected):,} sentences")
        print(f"   - With LOC also: {with_loc:,}")
        print(f"   - With PER only: {len(selected) - with_loc:,}")
        
        return selected
    
    def generate_nik(self):
        """Generate synthetic NIK"""
        prov = random.randint(11, 94)
        kab = random.randint(1, 99)
        kec = random.randint(1, 99)
        dd = random.randint(1, 28)
        if random.random() > 0.5:
            dd += 40
        mm = random.randint(1, 12)
        yy = random.randint(50, 99)
        nnnn = random.randint(1, 9999)
        return f"{prov:02d}{kab:02d}{kec:02d}{dd:02d}{mm:02d}{yy:02d}{nnnn:04d}"
    
    def generate_phone(self):
        """Generate synthetic phone"""
        prefixes = ['0812', '0813', '0821', '0852', '0856', '0817', '0855']
        prefix = random.choice(prefixes)
        suffix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        if random.random() < 0.3:
            return f"+62{prefix[1:]}{suffix}"
        return f"{prefix}{suffix}"
    
    def find_per_end_position(self, labels):
        """
        Find position akhir dari B-PER + I-PER continuous.
        Returns: index dari token TERAKHIR PER entity, atau -1 jika tidak ada.
        """
        last_per_idx = -1
        in_per = False
        
        for i, label in enumerate(labels):
            if label == 'B-NAMA':
                last_per_idx = i
                in_per = True
            elif label == 'I-NAMA' and in_per:
                last_per_idx = i
            else:
                in_per = False
        
        return last_per_idx
    
    def inject_pii(self, sentence_data):
        """
        Inject NIK & PHONE dengan BIO consistency yang benar.
        
        Strategi:
        - 60% inject NIK (di akhir kalimat untuk safety)
        - 60% inject PHONE (di akhir kalimat)
        """
        tokens = list(sentence_data['tokens'])
        tags = list(sentence_data['tags'])
        
        # Map ke PII labels (dengan blacklist filter)
        pii_labels = self.map_to_pii_labels(tokens, tags)
        
        # Fix BIO consistency
        pii_labels = self.fix_bio_consistency(pii_labels)
        
        # Decision: inject NIK & PHONE
        inject_nik = random.random() < 0.6
        inject_phone = random.random() < 0.6
        
        injected_nik = None
        injected_phone = None
        
        # REVISED: Inject di akhir saja untuk safety BIO
        if inject_nik:
            injected_nik = self.generate_nik()
            tokens.extend(['NIK', ':', injected_nik])
            pii_labels.extend(['O', 'O', 'B-NIK'])
        
        if inject_phone:
            injected_phone = self.generate_phone()
            tokens.extend(['HP', ':', injected_phone])
            pii_labels.extend(['O', 'O', 'B-PHONE'])
        
        # Reconstruct payload
        payload = ' '.join(tokens)
        
        # Build pii_data dari labels (untuk validation)
        pii_data = {}
        
        # Extract NAMA
        nama_tokens = []
        in_nama = False
        for tok, lab in zip(tokens, pii_labels):
            if lab == 'B-NAMA':
                if nama_tokens and not in_nama:
                    pass  # save previous (shouldn't happen here)
                nama_tokens = [tok]
                in_nama = True
            elif lab == 'I-NAMA' and in_nama:
                nama_tokens.append(tok)
            else:
                if nama_tokens and in_nama:
                    pii_data['nama'] = ' '.join(nama_tokens)
                    in_nama = False
        if nama_tokens and in_nama:
            pii_data['nama'] = ' '.join(nama_tokens)
        
        # Extract LOKASI
        lokasi_tokens = []
        in_lokasi = False
        for tok, lab in zip(tokens, pii_labels):
            if lab == 'B-LOKASI':
                if lokasi_tokens and not in_lokasi:
                    pass
                lokasi_tokens = [tok]
                in_lokasi = True
            elif lab == 'I-LOKASI' and in_lokasi:
                lokasi_tokens.append(tok)
            else:
                if lokasi_tokens and in_lokasi:
                    pii_data['lokasi'] = ' '.join(lokasi_tokens)
                    in_lokasi = False
        if lokasi_tokens and in_lokasi:
            pii_data['lokasi'] = ' '.join(lokasi_tokens)
        
        # Add injected
        if injected_nik:
            pii_data['nik'] = injected_nik
        if injected_phone:
            pii_data['telepon'] = injected_phone
        
        return {
            'payload': payload,
            'tokens': tokens,
            'labels': pii_labels,
            'pii_data': pii_data if pii_data else None,
            'format': 'naturalistic-nergrit',
            'source': 'nergrit_adapted'
        }
    
    def validate_sample(self, sample):
        """Validate BIO consistency of a sample"""
        labels = sample['labels']
        for i, label in enumerate(labels):
            if label.startswith('I-'):
                entity = label[2:]
                if i == 0:
                    return False
                prev = labels[i-1]
                if prev != f'B-{entity}' and prev != f'I-{entity}':
                    return False
        return True
    
    def adapt_to_pii_format(self, selected_sentences):
        """Adapt selected sentences ke PII format"""
        print(f"\n🔄 Adapting NERGrit sentences to PII format...")
        
        adapted = []
        invalid_count = 0
        
        for sent_data in tqdm(selected_sentences, desc="Adapting"):
            adapted_sample = self.inject_pii(sent_data)
            
            # Validate
            if self.validate_sample(adapted_sample):
                adapted.append(adapted_sample)
            else:
                invalid_count += 1
        
        if invalid_count > 0:
            print(f"   ⚠️  {invalid_count} samples skipped due to BIO inconsistency")
        
        return adapted


def main():
    print("="*70)
    print("  📚 NERGRIT CORPUS LOADER & ADAPTER (v2 - Revised)")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*70)
    
    print("\n📖 References:")
    print("   - NERGrit Corpus by PT Gria Inovasi Teknologi (GRIT)")
    print("   - HuggingFace: grit-id/id_nergrit_corpus")
    print("   - License: Public access")
    
    print("\n🆕 v2 Improvements:")
    print("   - Strict filter: only B-PER (Person)")
    print("   - GPE excluded (avoid OJK, Dinas false positives)")
    print("   - LOCATION blacklist for organizations")
    print("   - BIO consistency validation")
    print("   - Injection at end of sentence (safer BIO)")
    
    adapter = NERGritAdapterV2()
    
    if not adapter.download_nergrit():
        print("\n❌ Failed to download.")
        return
    
    selected = adapter.filter_relevant_sentences(n_target=500)
    adapted_data = adapter.adapt_to_pii_format(selected)
    
    df = pd.DataFrame(adapted_data)
    
    # Save
    os.makedirs('data/test_holdout', exist_ok=True)
    pkl_path = 'data/test_holdout/nergrit_adapted.pkl'
    csv_path = 'data/test_holdout/nergrit_adapted.csv'
    
    df.to_pickle(pkl_path)
    
    df_csv = df.copy()
    df_csv['pii_data'] = df_csv['pii_data'].apply(
        lambda x: json.dumps(x, ensure_ascii=False) if x else None
    )
    df_csv['tokens'] = df_csv['tokens'].apply(lambda x: ' | '.join(x))
    df_csv['labels'] = df_csv['labels'].apply(lambda x: ' | '.join(x))
    df_csv.to_csv(csv_path, index=False, encoding='utf-8')
    
    # Statistics
    print("\n" + "="*70)
    print("  📈 NERGRIT ADAPTED STATISTICS (v2)")
    print("="*70)
    print(f"  Total samples: {len(df)}")
    
    entity_counts = Counter()
    for labels in df['labels']:
        for label in labels:
            if label != 'O':
                entity_counts[label] += 1
    
    print(f"\n  Entity distribution:")
    for label in sorted(entity_counts.keys()):
        print(f"     {label:<12} : {entity_counts[label]:>5}")
    
    # BIO consistency check
    inconsistent = 0
    for labels in df['labels']:
        prev_entity = None
        for i, label in enumerate(labels):
            if label.startswith('I-'):
                entity = label[2:]
                if i == 0 or prev_entity != entity:
                    inconsistent += 1
                    break
                prev_entity = entity
            elif label.startswith('B-'):
                prev_entity = label[2:]
            else:
                prev_entity = None
    
    print(f"\n  BIO Consistency: {len(df) - inconsistent}/{len(df)} valid")
    
    # Show samples (avoid weird ones)
    print(f"\n  📝 Sample outputs (corrected):")
    print("  " + "-"*66)
    
    samples_shown = 0
    for i in range(len(df)):
        if samples_shown >= 3:
            break
        
        sample = df.iloc[i]
        # Only show samples with proper NAMA
        if not sample['pii_data'] or 'nama' not in sample['pii_data']:
            continue
        
        print(f"\n  Sample {samples_shown + 1}:")
        print(f"  Payload: {sample['payload'][:130]}...")
        
        entities = []
        for tok, lab in zip(sample['tokens'], sample['labels']):
            if lab != 'O':
                entities.append((tok, lab))
        
        if entities:
            print(f"  Entities ({len(entities)}):")
            for tok, lab in entities[:8]:
                print(f"     '{tok}' -> {lab}")
        
        samples_shown += 1
    
    print(f"\n  ✅ Saved: {pkl_path}")
    print(f"  ✅ Saved: {csv_path}")
    print("="*70)


if __name__ == "__main__":
    main()