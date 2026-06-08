"""
Hard Adversarial Generator: 500 truly challenging samples
Tugas Akhir: Arga Ariyuda Avian (2221101774)

LANDASAN ILMIAH:
- Goodfellow et al. (2015) - Explaining adversarial examples
- Wei & Zou (2019) - Easy data augmentation for NER  
- Yang & Eisner (2018) - Hand-crafted features vs learned features

STRATEGI 4 KATEGORI ADVERSARIAL:
1. CONTEXT-FREE 16-digit (no Order/Invoice keywords)
2. AMBIGUOUS NIK-like in unusual context
3. NESTED PII (PII di dalam non-PII context)
4. PARTIAL MATCH attempts (15 or 17 digit, near-pattern)
"""
import os
import random
import json
import pandas as pd
from faker import Faker
from tqdm import tqdm

SEED = 123  # Different seed
random.seed(SEED)
fake = Faker('id_ID')
Faker.seed(SEED)


class HardAdversarialGenerator:
    """Generate truly challenging adversarial samples"""
    
    def __init__(self):
        self.gov_jobs = [
            "Camat", "Lurah", "Kepala Dinas Pendidikan",
            "Sekretaris Daerah", "Kepala Bagian Umum"
        ]
        
        self.locations = [
            "Jakarta", "Bandung", "Surabaya", "Yogyakarta"
        ]
    
    def gen_nik(self):
        return ''.join([str(random.randint(0,9)) for _ in range(16)])
    
    def gen_phone(self):
        prefix = random.choice(['0812', '0813', '0852'])
        suffix = ''.join([str(random.randint(0,9)) for _ in range(8)])
        return prefix + suffix
    
    # =========================================================================
    # CATEGORY 1: CONTEXT-FREE 16-DIGIT (no clear context clues)
    # =========================================================================
    def gen_context_free_16digit(self):
        """16-digit non-NIK tanpa keyword Order/Invoice/Tracking"""
        fake_num = ''.join([str(random.randint(0,9)) for _ in range(16)])
        
        # No clear context clue
        templates = [
            f"{fake_num} - data record",
            f"Code {fake_num} verified",
            f"Status: {fake_num} active",
            f"Reference {fake_num} acknowledged",
            f"Entry {fake_num}",
            f"Auth token: {fake_num}",
            f"Session ID {fake_num}",
            f"Hash value: {fake_num}",
            f"UUID-like: {fake_num}",
            f"{fake_num} dalam database"
        ]
        
        return {
            'payload': random.choice(templates),
            'format': 'hard_adversarial',
            'pii_data': None,  # NOT a NIK
            'category': 'context_free_16digit'
        }
    
    # =========================================================================
    # CATEGORY 2: NIK in UNUSUAL CONTEXT (true NIK but suspicious)
    # =========================================================================
    def gen_nik_unusual_context(self):
        """True NIK tapi konteks tidak biasa"""
        nik = self.gen_nik()
        nama = fake.name()
        
        templates = [
            # NIK without label
            f"{nama} {nik}",  # No "NIK:" prefix
            f"{nik} - {nama}",  # NIK first
            f"Reg: {nik} | {nama}",  # Unusual prefix
            f"({nik}) {nama} telah terdaftar",
            f"#{nik} {nama}"
        ]
        
        return {
            'payload': random.choice(templates),
            'format': 'hard_adversarial',
            'pii_data': {'nik': nik, 'nama': nama},
            'category': 'nik_unusual_context'
        }
    
    # =========================================================================
    # CATEGORY 3: NESTED PII (PII inside non-PII context)
    # =========================================================================
    def gen_nested_pii(self):
        """PII bersarang dalam konteks lain"""
        nik = self.gen_nik()
        nama = fake.name()
        phone = self.gen_phone()
        
        # PII inside JSON arrays, logs, etc.
        templates = [
            f'metadata = {{"timestamp": "2026-01-15", "user": "{nama}", "id": "{nik}"}}',
            f"User-Agent: Mozilla/5.0 (X11; Linux) UserID:{nik} {nama}",
            f"<event type='login'><user nik='{nik}'>{nama}</user><tel>{phone}</tel></event>",
            f"console.log('user', '{nama}', 'id', '{nik}');"
        ]
        
        return {
            'payload': random.choice(templates),
            'format': 'hard_adversarial',
            'pii_data': {'nik': nik, 'nama': nama, 'telepon': phone},
            'category': 'nested_pii'
        }
    
    # =========================================================================
    # CATEGORY 4: NEAR-PATTERN (15 or 17 digit, not exactly NIK)
    # =========================================================================
    def gen_near_pattern(self):
        """Hampir mirip pattern tapi tidak persis"""
        # 15 digit (NOT NIK)
        fake15 = ''.join([str(random.randint(0,9)) for _ in range(15)])
        # 17 digit (NOT NIK)  
        fake17 = ''.join([str(random.randint(0,9)) for _ in range(17)])
        # Real NIK
        real_nik = self.gen_nik()
        
        templates = [
            # 15 digit (should NOT be NIK)
            f"Almost NIK: {fake15} (only 15 digits)",
            f"Code {fake15} - format mirip NIK tapi bukan",
            f"ID {fake15} (invalid format)",
            # 17 digit (should NOT be NIK)
            f"Long number: {fake17} (17 digits, too many)",
            f"{fake17} - tracking",
        ]
        
        return {
            'payload': random.choice(templates),
            'format': 'hard_adversarial',
            'pii_data': None,  # NOT a NIK (15 or 17 digit)
            'category': 'near_pattern'
        }
    
    # =========================================================================
    # MAIN GENERATOR
    # =========================================================================
    
    def generate_dataset(self, n_samples=500):
        print(f"\n📊 Generating {n_samples} HARD adversarial samples...\n")
        
        # 4 kategori dengan distribusi merata
        n_per_cat = n_samples // 4
        
        data = []
        
        for _ in tqdm(range(n_per_cat), desc="Context-free 16d"):
            data.append(self.gen_context_free_16digit())
        for _ in tqdm(range(n_per_cat), desc="NIK unusual ctx "):
            data.append(self.gen_nik_unusual_context())
        for _ in tqdm(range(n_per_cat), desc="Nested PII      "):
            data.append(self.gen_nested_pii())
        for _ in tqdm(range(n_samples - 3*n_per_cat), desc="Near pattern    "):
            data.append(self.gen_near_pattern())
        
        df = pd.DataFrame(data)
        df['source'] = 'hard_adversarial'
        df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
        
        return df


def main():
    print("="*70)
    print("  🔥 HARD ADVERSARIAL GENERATOR")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*70)
    
    print("\n📚 STRATEGI:")
    print("   1. Context-free 16-digit (no Order/Invoice keywords)")
    print("   2. NIK in unusual context")
    print("   3. Nested PII in non-PII container")
    print("   4. Near-pattern (15 or 17 digit)")
    
    generator = HardAdversarialGenerator()
    df = generator.generate_dataset(n_samples=500)
    
    # Save
    os.makedirs('data/raw', exist_ok=True)
    df.to_pickle('data/raw/hard_adversarial.pkl')
    
    df_csv = df.copy()
    df_csv['pii_data'] = df_csv['pii_data'].apply(
        lambda x: json.dumps(x, ensure_ascii=False) if x else None
    )
    df_csv.to_csv('data/raw/hard_adversarial.csv', index=False, encoding='utf-8')
    
    # Statistics
    print("\n" + "="*70)
    print("  📈 HARD ADVERSARIAL STATISTICS")
    print("="*70)
    print(f"  Total samples: {len(df)}")
    
    print(f"\n  Per-category:")
    for cat, count in df['category'].value_counts().items():
        print(f"     {cat:<25}: {count}")
    
    no_pii = df['pii_data'].isnull().sum()
    print(f"\n  Without PII (should NOT detect): {no_pii}")
    print(f"  With PII (should detect): {len(df) - no_pii}")
    
    print(f"\n  📝 Sample examples:")
    for cat in df['category'].unique():
        sample = df[df['category'] == cat].iloc[0]
        print(f"\n  [{cat}]")
        print(f"  {sample['payload']}")
        print(f"  PII: {sample['pii_data']}")
    
    print(f"\n  ✅ Saved: data/raw/hard_adversarial.pkl")
    print("="*70)


if __name__ == "__main__":
    main()