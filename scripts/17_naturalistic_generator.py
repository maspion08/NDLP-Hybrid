"""
Synthetic-Naturalistic Held-Out Test Set Generator
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Menghasilkan 1.000 sampel held-out test set dengan format payload jaringan
yang merepresentasikan kondisi real-world heterogen.

LANDASAN ILMIAH:
================
Pendekatan ini mengikuti best practice dalam literature PII detection terbaru:

1. PANORAMA (Mishra et al., 2025) - arXiv:2505.12238
   "Profile-driven, context-aware generation framework... captures the 
   contextual diversity and naturalistic occurrence of PII"
   → 6 content types: wiki, social media, forum, reviews, comments, marketplace

2. SPY Dataset (Savkin et al., 2025) - NAACL 2025
   "Novel synthetic dataset for PII detection... emulates real-world PII scenarios"

3. Gretel Synthetic PII Dataset (2024)
   "Coverage across 100 distinct financial document formats, with 20 specific 
   subtypes for each format – everything from customer support logs to..."
   → Document format diversity for evaluation robustness

4. Mendeley Synthetic PII Financial Dataset (2024)
   "Each entry simulates real-world financial texts such as auditor reports, 
   tax filings, compliance notices, and transaction confirmations"

ALIGNMENT DENGAN PROPOSAL TA:
============================
Sesuai Bab III.3.c.1 Proposal:
- Held-out test set 1.000 sampel ✓
- Format payload merepresentasikan lalu lintas jaringan aktif ✓
- Multi-format: structured + unstructured ✓
- Independent dari training distribution ✓

DISTRIBUSI 7 FORMAT REAL-WORLD:
==============================
1. Email Signature (150 samples)
2. Database/CSV Export (150 samples)
3. Customer Service Log (150 samples)
4. Government Letter Format (150 samples)
5. JSON Streaming Log (150 samples)
6. Tabular CSV/TSV Format (150 samples)
7. Multi-PII Mixed Context (100 samples)
"""
import os
import json
import random
import pandas as pd
from faker import Faker
from urllib.parse import quote
from datetime import datetime, timedelta
from tqdm import tqdm

# Reproducibility (different seed dari training data untuk independence)
SEED = 99
random.seed(SEED)
fake = Faker('id_ID')
Faker.seed(SEED)


class SyntheticNaturalisticGenerator:
    """
    Generator held-out test set dengan format payload jaringan real-world.
    
    Reference:
    - Mishra et al. (2025) PANORAMA: profile-driven naturalistic generation
    - Savkin et al. (2025) SPY: synthetic PII detection benchmark
    - Gretel.ai (2024): document format diversity for robust evaluation
    """
    
    def __init__(self):
        # Daftar jabatan (campur government & private untuk diversity)
        self.gov_jobs = [
            "Kepala Dinas Pendidikan", "Kepala Dinas Kesehatan",
            "Sekretaris Daerah", "Asisten Sekretaris Daerah",
            "Camat", "Lurah", "Kepala Bagian Umum",
            "Kepala Bidang Anggaran", "Staf Administrasi"
        ]
        
        self.locations = [
            "Jakarta", "Bandung", "Surabaya", "Yogyakarta", "Semarang",
            "Medan", "Makassar", "Depok", "Bogor", "Tangerang", "Bekasi",
            "Palembang", "Denpasar", "Malang", "Padang", "Pekanbaru",
            "Banjarmasin", "Pontianak", "Manado", "Aceh", "Riau", "Bali",
            "Jawa Barat", "Jawa Tengah", "Jawa Timur"
        ]
        
        self.phone_prefixes = [
            '0811', '0812', '0813', '0821', '0822', '0823',
            '0851', '0852', '0853', '0855', '0856', '0857',
            '0817', '0818', '0819', '0814', '0815', '0816'
        ]
    
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
        """Generate synthetic Indonesian phone"""
        prefix = random.choice(self.phone_prefixes)
        suffix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        if random.random() < 0.3:
            return f"+62{prefix[1:]}{suffix}"
        return f"{prefix}{suffix}"
    
    def generate_pii_set(self):
        """Generate complete PII set"""
        return {
            'nik': self.generate_nik(),
            'nama': fake.name(),
            'telepon': self.generate_phone(),
            'jabatan': random.choice(self.gov_jobs),
            'lokasi': random.choice(self.locations)
        }
    
    # =========================================================================
    # FORMAT 1: EMAIL SIGNATURE
    # =========================================================================
    def gen_email_signature(self):
        """
        Real-world format: Email signature dengan PII.
        Reference: Common professional email format.
        """
        pii = self.generate_pii_set()
        
        templates = [
            f"Hormat saya,\n\n{pii['nama']}\n{pii['jabatan']}\nKantor: {pii['lokasi']}\nNIK: {pii['nik']}\nHP: {pii['telepon']}",
            
            f"Best regards,\n\n{pii['nama']} | {pii['jabatan']}\nLokasi: {pii['lokasi']}\nID: {pii['nik']}\nMobile: {pii['telepon']}",
            
            f"Salam hangat,\n{pii['nama']}\nNIK: {pii['nik']}\n{pii['jabatan']} - {pii['lokasi']}\nTelepon: {pii['telepon']}",
            
            f"Terima kasih,\n\n{pii['nama']} ({pii['jabatan']})\n📧 NIK: {pii['nik']}\n📱 {pii['telepon']}\n📍 {pii['lokasi']}"
        ]
        
        return {
            'payload': random.choice(templates),
            'format': 'email_signature',
            'pii_data': pii
        }
    
    # =========================================================================
    # FORMAT 2: DATABASE/CSV EXPORT
    # =========================================================================
    def gen_database_export(self):
        """
        Real-world format: Database export atau CSV row.
        Reference: Gretel.ai dataset includes database exports.
        """
        pii = self.generate_pii_set()
        record_id = random.randint(1000, 9999)
        
        templates = [
            # CSV row
            f"{record_id},{pii['nik']},{pii['nama']},{pii['jabatan']},{pii['lokasi']},{pii['telepon']}",
            
            # Pipe-delimited
            f"{record_id}|{pii['nik']}|{pii['nama']}|{pii['jabatan']}|{pii['lokasi']}|{pii['telepon']}",
            
            # SQL Insert
            f"INSERT INTO pegawai (id, nik, nama, jabatan, lokasi, telepon) VALUES ({record_id}, '{pii['nik']}', '{pii['nama']}', '{pii['jabatan']}', '{pii['lokasi']}', '{pii['telepon']}');",
            
            # Database log
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] DB_INSERT: id={record_id}; nik={pii['nik']}; nama={pii['nama']}; jabatan={pii['jabatan']}; lokasi={pii['lokasi']}; telepon={pii['telepon']}"
        ]
        
        return {
            'payload': random.choice(templates),
            'format': 'database_export',
            'pii_data': pii
        }
    
    # =========================================================================
    # FORMAT 3: CUSTOMER SERVICE LOG
    # =========================================================================
    def gen_cs_log(self):
        """
        Real-world format: Customer service interaction log.
        Reference: Gretel.ai mentions "customer support logs" as one of 100 formats.
        """
        pii = self.generate_pii_set()
        timestamp = datetime.now() - timedelta(days=random.randint(1, 30))
        ts_str = timestamp.strftime('%Y-%m-%d %H:%M')
        
        templates = [
            f"[{ts_str}] CS_AGENT: Validasi pelanggan - Nama: {pii['nama']}, NIK: {pii['nik']}, HP: {pii['telepon']}, Lokasi: {pii['lokasi']}, Jabatan: {pii['jabatan']}",
            
            f"[{ts_str}] LOG: Pelanggan {pii['nama']} (NIK: {pii['nik']}) menelepon dari nomor {pii['telepon']}. Domisili: {pii['lokasi']}. Profesi: {pii['jabatan']}.",
            
            f"TICKET #{random.randint(1000, 9999)} - {ts_str}\nPelanggan: {pii['nama']}\nNIK: {pii['nik']}\nKontak: {pii['telepon']}\nKota: {pii['lokasi']}\nJabatan: {pii['jabatan']}",
            
            f"<{ts_str}> Helpdesk berbicara dengan {pii['nama']} (HP {pii['telepon']}, NIK {pii['nik']}, {pii['jabatan']} di {pii['lokasi']})"
        ]
        
        return {
            'payload': random.choice(templates),
            'format': 'cs_log',
            'pii_data': pii
        }
    
    # =========================================================================
    # FORMAT 4: GOVERNMENT LETTER FORMAT
    # =========================================================================
    def gen_gov_letter(self):
        """
        Real-world format: Surat resmi pemerintah.
        Reference: Mendeley dataset includes "compliance notices" type.
        """
        pii = self.generate_pii_set()
        
        templates = [
            f"Yang bertanda tangan di bawah ini:\n\nNama         : {pii['nama']}\nNIK          : {pii['nik']}\nJabatan      : {pii['jabatan']}\nWilayah Kerja: {pii['lokasi']}\nNo. Telepon  : {pii['telepon']}\n\ndengan ini menyatakan...",
            
            f"Surat Keterangan No. {random.randint(100, 999)}/SK/{random.randint(2024, 2026)}\n\nKepala kantor menerangkan bahwa {pii['nama']} dengan NIK {pii['nik']} adalah benar bertugas sebagai {pii['jabatan']} di {pii['lokasi']}. Yang bersangkutan dapat dihubungi pada nomor {pii['telepon']}.",
            
            f"PERMOHONAN AKSES SISTEM\n\nDari   : {pii['nama']}\nNIK    : {pii['nik']}\nUnit   : {pii['jabatan']}\nKantor : {pii['lokasi']}\nKontak : {pii['telepon']}\n\nMemohon akses sistem informasi kepegawaian.",
            
            f"BERITA ACARA - Pelaksanaan kegiatan dilakukan oleh Sdr/i {pii['nama']} (NIK: {pii['nik']}) selaku {pii['jabatan']} pada wilayah kerja {pii['lokasi']}. Untuk koordinasi lebih lanjut, dapat menghubungi {pii['telepon']}."
        ]
        
        return {
            'payload': random.choice(templates),
            'format': 'gov_letter',
            'pii_data': pii
        }
    
    # =========================================================================
    # FORMAT 5: JSON STREAMING LOG
    # =========================================================================
    def gen_json_log(self):
        """
        Real-world format: JSON application log.
        Reference: Common in microservices logging (ELK stack, etc).
        """
        pii = self.generate_pii_set()
        timestamp = datetime.now().isoformat()
        log_levels = ['INFO', 'DEBUG', 'WARN']
        
        templates = [
            json.dumps({
                "timestamp": timestamp,
                "level": random.choice(log_levels),
                "service": "user-service",
                "event": "user_registration",
                "user": {
                    "nik": pii['nik'],
                    "name": pii['nama'],
                    "phone": pii['telepon'],
                    "position": pii['jabatan'],
                    "location": pii['lokasi']
                }
            }, ensure_ascii=False),
            
            json.dumps({
                "@timestamp": timestamp,
                "log_type": "audit",
                "action": "data_access",
                "actor": {
                    "name": pii['nama'],
                    "id": pii['nik'],
                    "phone": pii['telepon']
                },
                "metadata": {
                    "department": pii['jabatan'],
                    "office": pii['lokasi']
                }
            }, ensure_ascii=False),
            
            f'{{"ts":"{timestamp}","msg":"User profile updated","data":{{"nik":"{pii["nik"]}","nama":"{pii["nama"]}","hp":"{pii["telepon"]}","jbt":"{pii["jabatan"]}","kt":"{pii["lokasi"]}"}}}}'
        ]
        
        return {
            'payload': random.choice(templates),
            'format': 'json_log',
            'pii_data': pii
        }
    
    # =========================================================================
    # FORMAT 6: TABULAR CSV/TSV FORMAT  
    # =========================================================================
    def gen_tabular_format(self):
        """
        Real-world format: Tabular data dengan header.
        Reference: Common in data exports from spreadsheets.
        """
        pii = self.generate_pii_set()
        
        templates = [
            # CSV with header
            f"nama,nik,telepon,jabatan,lokasi\n{pii['nama']},{pii['nik']},{pii['telepon']},{pii['jabatan']},{pii['lokasi']}",
            
            # TSV with header
            f"nama\tnik\ttelepon\tjabatan\tlokasi\n{pii['nama']}\t{pii['nik']}\t{pii['telepon']}\t{pii['jabatan']}\t{pii['lokasi']}",
            
            # Pipe with header
            f"nama|nik|telepon|jabatan|lokasi\n{pii['nama']}|{pii['nik']}|{pii['telepon']}|{pii['jabatan']}|{pii['lokasi']}",
            
            # Markdown table
            f"| Nama | NIK | Telepon | Jabatan | Lokasi |\n|------|-----|---------|---------|--------|\n| {pii['nama']} | {pii['nik']} | {pii['telepon']} | {pii['jabatan']} | {pii['lokasi']} |"
        ]
        
        return {
            'payload': random.choice(templates),
            'format': 'tabular',
            'pii_data': pii
        }
    
    # =========================================================================
    # FORMAT 7: MULTI-PII MIXED CONTEXT
    # =========================================================================
    def gen_multi_context(self):
        """
        Real-world format: Multiple PII in narrative context.
        Reference: PANORAMA (2025) emphasizes "naturalistic context" with PII.
        """
        pii = self.generate_pii_set()
        # Generate second person for richer context
        pii2 = self.generate_pii_set()
        
        templates = [
            f"Mohon konfirmasi dari {pii['nama']} (NIK: {pii['nik']}, HP: {pii['telepon']}) selaku {pii['jabatan']} di {pii['lokasi']}, mengenai permohonan akses dari {pii2['nama']} dengan NIK {pii2['nik']}.",
            
            f"Komunikasi internal: {pii['jabatan']} {pii['nama']} di {pii['lokasi']} (kontak {pii['telepon']}, NIK {pii['nik']}) telah menyetujui permintaan dari rekan kerja.",
            
            f"Dalam meeting koordinasi, {pii['nama']} (NIK {pii['nik']}) sebagai {pii['jabatan']} dari {pii['lokasi']} menyampaikan laporan. Beliau dapat dihubungi di {pii['telepon']} untuk keperluan tindak lanjut."
        ]
        
        # Multi-context: hanya track PII pertama (yang dominant)
        return {
            'payload': random.choice(templates),
            'format': 'multi_context',
            'pii_data': pii  # Hanya track PII utama
        }
    
    # =========================================================================
    # MAIN GENERATOR
    # =========================================================================
    
    def generate_dataset(self, n_samples=1000):
        """Generate held-out test set sesuai distribusi"""
        print(f"\n📊 Generating {n_samples} synthetic-naturalistic samples...\n")
        
        # Distribusi 7 format
        # Email Sig, DB Export, CS Log, Gov Letter, JSON Log, Tabular, Multi-Context
        distribution = {
            'email_sig': 150,
            'db_export': 150,
            'cs_log': 150,
            'gov_letter': 150,
            'json_log': 150,
            'tabular': 150,
            'multi_context': 100
        }
        
        # Adjust ke total n_samples jika berbeda
        total = sum(distribution.values())
        if total != n_samples:
            scale = n_samples / total
            distribution = {k: int(v * scale) for k, v in distribution.items()}
            # Adjust total ke n_samples
            diff = n_samples - sum(distribution.values())
            distribution['multi_context'] += diff
        
        for fmt, count in distribution.items():
            print(f"   📌 {fmt:<15}: {count:>4}")
        print()
        
        data = []
        
        for _ in tqdm(range(distribution['email_sig']), desc="Email Sig "):
            data.append(self.gen_email_signature())
        for _ in tqdm(range(distribution['db_export']), desc="DB Export "):
            data.append(self.gen_database_export())
        for _ in tqdm(range(distribution['cs_log']), desc="CS Log    "):
            data.append(self.gen_cs_log())
        for _ in tqdm(range(distribution['gov_letter']), desc="Gov Letter"):
            data.append(self.gen_gov_letter())
        for _ in tqdm(range(distribution['json_log']), desc="JSON Log  "):
            data.append(self.gen_json_log())
        for _ in tqdm(range(distribution['tabular']), desc="Tabular   "):
            data.append(self.gen_tabular_format())
        for _ in tqdm(range(distribution['multi_context']), desc="Multi-Ctx "):
            data.append(self.gen_multi_context())
        
        df = pd.DataFrame(data)
        df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
        df['source'] = 'synthetic_naturalistic'
        
        return df


def main():
    print("="*70)
    print("  🎯 SYNTHETIC-NATURALISTIC HELD-OUT TEST SET GENERATOR")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*70)
    
    print("\n📚 LANDASAN ILMIAH:")
    print("   1. PANORAMA (Mishra et al., 2025) arXiv:2505.12238")
    print("      → Profile-driven naturalistic generation")
    print("   2. SPY Dataset (Savkin et al., 2025) NAACL 2025")
    print("      → Synthetic PII detection benchmark")
    print("   3. Gretel Synthetic PII (2024)")
    print("      → 100+ document format diversity")
    print("   4. Mendeley Synthetic PII Financial (2024)")
    print("      → Real-world document simulation")
    
    print("\n🎯 TUJUAN:")
    print("   - Held-out test set untuk evaluasi generalisasi")
    print("   - 7 format real-world berbeda")
    print("   - Independent dari training distribution (seed=99)")
    print("   - Sesuai proposal Bab III.3.c.1 (1.000 sampel held-out)")
    
    generator = SyntheticNaturalisticGenerator()
    df = generator.generate_dataset(n_samples=1000)
    
    # Save
    os.makedirs('data/test_holdout', exist_ok=True)
    pkl_path = 'data/test_holdout/naturalistic.pkl'
    csv_path = 'data/test_holdout/naturalistic.csv'
    
    df.to_pickle(pkl_path)
    
    df_csv = df.copy()
    df_csv['pii_data'] = df_csv['pii_data'].apply(
        lambda x: json.dumps(x, ensure_ascii=False) if x else None
    )
    df_csv.to_csv(csv_path, index=False, encoding='utf-8')
    
    # Statistics
    print("\n" + "="*70)
    print("  📈 NATURALISTIC DATASET STATISTICS")
    print("="*70)
    print(f"  Total samples: {len(df)}")
    
    print(f"\n  Distribusi format:")
    for fmt, count in df['format'].value_counts().sort_index().items():
        pct = (count/len(df))*100
        print(f"     {fmt:<15} : {count:>4} ({pct:>4.1f}%)")
    
    # PII coverage
    has_pii = df['pii_data'].notna().sum()
    print(f"\n  Samples with PII: {has_pii}/{len(df)}")
    
    # Show samples
    print(f"\n  📝 Sample outputs per format:")
    print("  " + "-"*66)
    
    for fmt in df['format'].unique():
        sample = df[df['format'] == fmt].iloc[0]
        print(f"\n  [{fmt.upper()}]")
        preview = sample['payload'][:200].replace('\n', ' | ')
        print(f"  {preview}...")
    
    print(f"\n  ✅ Saved: {pkl_path}")
    print(f"  ✅ Saved: {csv_path}")
    print("="*70)


if __name__ == "__main__":
    main()