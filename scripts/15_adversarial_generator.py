"""
Adversarial Sample Generator
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Membuat 1.000 adversarial samples untuk meningkatkan robustness model.
4 kategori adversarial sesuai best practices NER literature:

1. False Positive Triggers (300 samples)
   - 16-digit numbers in non-PII context
   - Phone-like patterns yang bukan PII

2. Out-of-Vocabulary Entities (300 samples)
   - Private sector job titles
   - Foreign locations
   - Non-standard names

3. Mixed Format Payloads (200 samples)
   - URL parameters
   - XML/HTML tags
   - SQL queries

4. Edge Linguistic Cases (200 samples)
   - Typos & abbreviations
   - Bilingual contexts

Referensi:
- Smith et al. (2024) - Sample size for NER fine-tuning
- BigCode (2023) - PII detection adversarial cases
"""
import os
import random
import json
import pandas as pd
from faker import Faker
from urllib.parse import quote
from tqdm import tqdm

# Reproducibility
SEED = 42
random.seed(SEED)
fake = Faker('id_ID')
Faker.seed(SEED)


class AdversarialGenerator:
    """Generator untuk adversarial samples"""
    
    def __init__(self):
        # === Out-of-Vocabulary Data ===
        self.private_jobs = [
            "Manajer Operasional", "Manajer Senior", "Direktur Keuangan",
            "CEO", "CFO", "CTO", "COO",
            "Software Engineer", "Data Analyst", "Product Manager",
            "Marketing Manager", "Sales Director", "HR Manager",
            "Konsultan IT", "Software Developer", "Project Manager",
            "Business Analyst", "Account Executive", "Marketing Specialist",
            "Senior Developer", "Junior Developer", "DevOps Engineer",
            "Quality Assurance", "Tech Lead", "Engineering Manager"
        ]
        
        self.foreign_locations = [
            "Singapore", "Malaysia", "Thailand", "Vietnam", "Filipina",
            "Tokyo", "Seoul", "Beijing", "Shanghai", "Hong Kong",
            "Sydney", "Melbourne", "London", "Paris", "Berlin",
            "New York", "San Francisco", "Los Angeles", "Toronto",
            "Dubai", "Doha", "Riyadh", "Mumbai", "Bangalore"
        ]
        
        # Indonesian government locations (untuk mix)
        self.gov_locations = [
            "Jakarta", "Bandung", "Surabaya", "Semarang", "Medan"
        ]
        
        self.gov_jobs = [
            "Camat", "Lurah", "Sekretaris Daerah",
            "Kepala Dinas Pendidikan", "Staf Administrasi"
        ]
    
    def generate_nik(self):
        """Generate NIK 16 digit"""
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
        """Generate Indonesian phone"""
        prefixes = ['0812', '0813', '0821', '0852', '0856', '0817']
        prefix = random.choice(prefixes)
        suffix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        if random.random() < 0.3:
            return f"+62{prefix[1:]}{suffix}"
        return f"{prefix}{suffix}"
    
    # =========================================================================
    # CATEGORY 1: FALSE POSITIVE TRIGGERS (300 samples)
    # =========================================================================
    
    def gen_false_positive_16digit(self):
        """16-digit number (Order ID, Invoice, dll) disebar ke multi-format"""
        fake_num = ''.join([str(random.randint(0, 9)) for _ in range(16)])
        format_type = random.choice(['json', 'formdata', 'narrative'])
        
        if format_type == 'json':
            templates = [
                f'{{"event": "checkout", "order_id": "{fake_num}", "status": "success"}}',
                f'{{"transaction": {{"id": "{fake_num}", "amount": 5000000}}}}',
                f'{{"log_data": {{"session_id": "{fake_num}", "action": "login"}}}}',
                f'{{"api_response": {{"reference_number": "{fake_num}", "code": 200}}}}'
            ]
        elif format_type == 'formdata':
            templates = [
                f"order_id={fake_num}&status=success&amount=5000000",
                f"trx_id={fake_num}&payment_method=transfer",
                f"session={fake_num}&action=checkout",
                f"ref_num={fake_num}&callback=true"
            ]
        else:
            templates = [
                f"Order ID: {fake_num} sudah berhasil diproses dan akan dikirim",
                f"Nomor invoice {fake_num} telah diterima sistem",
                f"Transaction ID: {fake_num} confirmed",
                f"Reference number: {fake_num} for your booking",
                f"Serial number perangkat: {fake_num}"
            ]
            
        return {
            'payload': random.choice(templates),
            'format': format_type,
            'pii_data': None,
            'category': 'context_free_16digit'
        }
    
    def gen_false_positive_phone_like(self):
        """Angka mirip phone tapi bukan PII"""
        # Generate amount-like number
        amount = random.randint(10000000, 999999999)
        
        templates = [
            f"Saldo akhir: Rp {amount:,}",
            f"Total transaksi: Rp {amount:,}",
            f"Tagihan listrik bulan ini: Rp {amount:,}",
            f"Harga produk: Rp {amount:,}",
            f"Limit kartu kredit: Rp {amount:,}",
            f"Jumlah bantuan sosial: Rp {amount:,}",
            f"Anggaran tahunan: Rp {amount:,}",
            f"Dana cadangan: Rp {amount:,}"
        ]
        
        return {
            'payload': random.choice(templates),
            'format': 'narrative',
            'pii_data': None
        }
    
    # =========================================================================
    # CATEGORY 2: OUT-OF-VOCABULARY ENTITIES (300 samples)
    # =========================================================================
    
    def gen_oov_private_job(self):
        """Jabatan private sector + nama + lokasi luar negeri"""
        nama = fake.name()
        nik = self.generate_nik()
        phone = self.generate_phone()
        job = random.choice(self.private_jobs)
        location = random.choice(self.foreign_locations)
        
        templates = [
            # JSON dengan jabatan private
            json.dumps({
                "nik": nik,
                "nama": nama,
                "telepon": phone,
                "jabatan": job,
                "kota": location
            }, ensure_ascii=False),
            
            # Form-data
            f"nik={nik}&nama={quote(nama)}&telepon={phone}&jabatan={quote(job)}&kota={quote(location)}",
            
            # Naratif
            f"Permohonan dari {nama} (NIK: {nik}) sebagai {job} yang berbasis di {location}. Kontak: {phone}",
            f"Data karyawan {nama} dengan NIK {nik} bekerja sebagai {job} di kantor {location}. HP: {phone}",
        ]
        
        format_type = random.choice(['json', 'formdata', 'narrative'])
        if format_type == 'json':
            payload = templates[0]
        elif format_type == 'formdata':
            payload = templates[1]
        else:
            payload = random.choice(templates[2:])
        
        return {
            'payload': payload,
            'format': format_type,
            'pii_data': {
                'nik': nik,
                'nama': nama,
                'telepon': phone,
                'jabatan': job,
                'lokasi': location
            }
        }
    
    def gen_oov_foreign_location(self):
        """Lokasi luar negeri dengan jabatan government"""
        nama = fake.name()
        nik = self.generate_nik()
        phone = self.generate_phone()
        job = random.choice(self.gov_jobs)
        location = random.choice(self.foreign_locations)
        
        templates = [
            f"Konsulat Jenderal RI: {nama} ({nik}) bertugas sebagai {job} di {location}. Telp: {phone}",
            f"Atase {job} {nama} (NIK: {nik}) ditempatkan di {location}. Kontak: {phone}",
            json.dumps({
                "nama_lengkap": nama,
                "nik": nik,
                "jabatan": job,
                "lokasi_tugas": location,
                "telepon": phone
            }, ensure_ascii=False)
        ]
        
        return {
            'payload': random.choice(templates),
            'format': random.choice(['narrative', 'json']),
            'pii_data': {
                'nik': nik,
                'nama': nama,
                'telepon': phone,
                'jabatan': job,
                'lokasi': location
            }
        }
    
    # =========================================================================
    # CATEGORY 3: MIXED FORMAT PAYLOADS (200 samples)
    # =========================================================================
    
    def gen_url_format(self):
        """URL parameter format"""
        nama = fake.name()
        nik = self.generate_nik()
        phone = self.generate_phone()
        
        templates = [
            f"https://example.com/api/user?nik={nik}&phone={phone}&name={quote(nama)}",
            f"GET /api/v1/users/{nik}?phone={phone}",
            f"https://gov-id.example.com/citizen?id={nik}&name={quote(nama)}&contact={phone}"
        ]
        
        return {
            'payload': random.choice(templates),
            'format': 'narrative',  # treat as text
            'pii_data': {
                'nik': nik,
                'nama': nama,
                'telepon': phone
            }
        }
    
    def gen_xml_format(self):
        """XML/HTML format"""
        nama = fake.name()
        nik = self.generate_nik()
        phone = self.generate_phone()
        job = random.choice(self.gov_jobs)
        location = random.choice(self.gov_locations)
        
        templates = [
            f"<user><nik>{nik}</nik><name>{nama}</name><phone>{phone}</phone></user>",
            f"<citizen id='{nik}'><name>{nama}</name><position>{job}</position><city>{location}</city></citizen>",
            f"<form><field name='nik'>{nik}</field><field name='nama'>{nama}</field><field name='telepon'>{phone}</field></form>"
        ]
        
        return {
            'payload': random.choice(templates),
            'format': 'narrative',
            'pii_data': {
                'nik': nik,
                'nama': nama,
                'telepon': phone,
                'jabatan': job,
                'lokasi': location
            }
        }
    
    def gen_sql_format(self):
        """SQL query format"""
        nama = fake.name()
        nik = self.generate_nik()
        phone = self.generate_phone()
        
        templates = [
            f"INSERT INTO users (nik, nama, phone) VALUES ('{nik}', '{nama}', '{phone}')",
            f"UPDATE citizens SET name='{nama}', phone='{phone}' WHERE nik='{nik}'",
            f"SELECT * FROM employees WHERE nik = '{nik}' AND nama LIKE '%{nama}%'"
        ]
        
        return {
            'payload': random.choice(templates),
            'format': 'narrative',
            'pii_data': {
                'nik': nik,
                'nama': nama,
                'telepon': phone
            }
        }
    
    # =========================================================================
    # CATEGORY 4: EDGE LINGUISTIC CASES (200 samples)
    # =========================================================================
    
    def gen_typo_abbreviation(self):
        """Typo dan singkatan"""
        nama = fake.name()
        nik = self.generate_nik()
        phone = self.generate_phone()
        job = random.choice(self.gov_jobs)
        location = random.choice(self.gov_locations)
        
        templates = [
            # Singkatan
            f"Nama: {nama}, Nik: {nik}, Tlp: {phone}, Jbtn: {job}, Kot: {location}",
            f"nm={nama}; nik={nik}; hp={phone}; jbt={job}; kt={location}",
            
            # Mixed case
            f"NIK milik {nama} (NIK: {nik}), Hp: {phone}, Jabatan: {job}, di {location}",
            
            # Typo
            f"Pegawai {nama}, NIK {nik}, telp {phone}, ditugaskan di {location} sbg {job}",
            f"Permintaan dari {nama} dgn NIK {nik}. Kontak {phone}. Posisi {job} di {location}"
        ]
        
        return {
            'payload': random.choice(templates),
            'format': 'narrative',
            'pii_data': {
                'nik': nik,
                'nama': nama,
                'telepon': phone,
                'jabatan': job,
                'lokasi': location
            }
        }
    
    def gen_bilingual_context(self):
        """Bilingual Indonesia-English context"""
        nama = fake.name()
        nik = self.generate_nik()
        phone = self.generate_phone()
        job = random.choice(self.private_jobs)
        location = random.choice(self.foreign_locations + self.gov_locations)
        
        templates = [
            f"Employee data: Name {nama}, NIK {nik}, Position {job}, Office {location}, Mobile {phone}",
            f"Permintaan registration untuk user {nama} (NIK: {nik}) sebagai {job} di {location}, contact {phone}",
            f"User registration form: nama={nama}, identity_number={nik}, role={job}, branch={location}, phone={phone}",
        ]
        
        return {
            'payload': random.choice(templates),
            'format': 'narrative',
            'pii_data': {
                'nik': nik,
                'nama': nama,
                'telepon': phone,
                'jabatan': job,
                'lokasi': location
            }
        }
    
    # =========================================================================
    # MAIN GENERATOR
    # =========================================================================
    
    def generate_dataset(self, n_samples=1000):
        """Generate adversarial dataset sesuai distribusi"""
        print(f"\n📊 Generating {n_samples} adversarial samples...\n")
        
        # Distribusi:
        # 30% False Positive (300)
        # 30% OOV Entities (300)
        # 20% Mixed Format (200)
        # 20% Edge Linguistic (200)
        
        n_fp = int(n_samples * 0.30)
        n_oov = int(n_samples * 0.30)
        n_mixed = int(n_samples * 0.20)
        n_edge = n_samples - n_fp - n_oov - n_mixed
        
        print(f"   📌 False Positive    : {n_fp:>4}")
        print(f"   📌 OOV Entities      : {n_oov:>4}")
        print(f"   📌 Mixed Format      : {n_mixed:>4}")
        print(f"   📌 Edge Linguistic   : {n_edge:>4}")
        print()
        
        data = []
        
        # Category 1: False Positive (split 50/50)
        for _ in tqdm(range(n_fp // 2), desc="FP-16digit "):
            data.append(self.gen_false_positive_16digit())
        for _ in tqdm(range(n_fp - n_fp // 2), desc="FP-PhoneLike"):
            data.append(self.gen_false_positive_phone_like())
        
        # Category 2: OOV (split 50/50)
        for _ in tqdm(range(n_oov // 2), desc="OOV-Job    "):
            data.append(self.gen_oov_private_job())
        for _ in tqdm(range(n_oov - n_oov // 2), desc="OOV-Location"):
            data.append(self.gen_oov_foreign_location())
        
        # Category 3: Mixed Format (split 1/3 each)
        per_format = n_mixed // 3
        for _ in tqdm(range(per_format), desc="Mixed-URL  "):
            data.append(self.gen_url_format())
        for _ in tqdm(range(per_format), desc="Mixed-XML  "):
            data.append(self.gen_xml_format())
        for _ in tqdm(range(n_mixed - 2*per_format), desc="Mixed-SQL  "):
            data.append(self.gen_sql_format())
        
        # Category 4: Edge Linguistic (split 50/50)
        for _ in tqdm(range(n_edge // 2), desc="Edge-Typo  "):
            data.append(self.gen_typo_abbreviation())
        for _ in tqdm(range(n_edge - n_edge // 2), desc="Edge-Biling"):
            data.append(self.gen_bilingual_context())
        
        df = pd.DataFrame(data)
        # Add adversarial marker
        df['source'] = 'adversarial'
        
        return df


def main():
    print("="*70)
    print("  🎯 ADVERSARIAL SAMPLE GENERATOR")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*70)
    
    generator = AdversarialGenerator()
    df = generator.generate_dataset(n_samples=1000)
    
    # Save
    os.makedirs('data/raw', exist_ok=True)
    pkl_path = 'data/raw/adversarial.pkl'
    csv_path = 'data/raw/adversarial.csv'
    
    df.to_pickle(pkl_path)
    
    df_csv = df.copy()
    df_csv['pii_data'] = df_csv['pii_data'].apply(
        lambda x: json.dumps(x, ensure_ascii=False) if x else None
    )
    df_csv.to_csv(csv_path, index=False, encoding='utf-8')
    
    # Statistics
    print("\n" + "="*70)
    print("  📈 ADVERSARIAL DATASET STATISTICS")
    print("="*70)
    print(f"  Total samples: {len(df)}")
    print(f"\n  Distribusi format:")
    for fmt, count in df['format'].value_counts().items():
        pct = (count/len(df))*100
        print(f"     {fmt:<12} : {count:>4} ({pct:>4.1f}%)")
    
    # Count samples without PII (false positive triggers)
    no_pii = df['pii_data'].isnull().sum()
    print(f"\n  Samples without PII (FP triggers): {no_pii}")
    print(f"  Samples with PII: {len(df) - no_pii}")
    
    print(f"\n  Examples per category:")
    print("  " + "-"*66)
    
    # Show 1 example per type
    print("\n  [FALSE POSITIVE (16-digit non-NIK)]")
    fp_samples = df[df['pii_data'].isnull()]
    if len(fp_samples) > 0:
        print(f"  {fp_samples.iloc[0]['payload']}")
    
    print("\n  [OOV - Private Sector Job]")
    oov_samples = df[df['pii_data'].notna()]
    private_jobs = ['Manajer', 'CEO', 'Software', 'Director']
    for _, row in oov_samples.iterrows():
        if row['pii_data'] and any(j in row['pii_data'].get('jabatan', '') for j in private_jobs):
            print(f"  {row['payload'][:130]}...")
            break
    
    print(f"\n  ✅ Saved: {pkl_path}")
    print(f"  ✅ Saved: {csv_path}")
    print("="*70)


if __name__ == "__main__":
    main()