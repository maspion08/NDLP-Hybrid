"""
Data Generator - Contextual Data Synthesis
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Sesuai Bab III.3.c.1 Proposal:
- 10.000 sampel sintetis
- Format: JSON, Form-Data, Naratif, Negatif
- Entitas: NIK, Phone, Nama, Jabatan, Lokasi
- Locale: id_ID (Indonesia)
- Reproducible (seed=42)

Penting: pii_data hanya berisi entity yang BENAR-BENAR ada di payload
         (untuk konsistensi dengan ground truth saat BIO tagging)
"""
from nik_utils import generate_nik as _generate_nik_valid
from faker import Faker
import pandas as pd
import random
import json
import os
import sys
from urllib.parse import quote
from tqdm import tqdm


# Reproducibility
SEED = 42
random.seed(SEED)
fake = Faker('id_ID')
Faker.seed(SEED)


class PiiDataGenerator:
    """Generator untuk dataset PII sintetis berbahasa Indonesia"""
    
    def __init__(self):
        # 70% Jabatan Pemerintahan (Konteks Utama)
        jabatan_pemerintah = [
            "Kepala Dinas Pendidikan", "Kepala Dinas Kesehatan", "Kepala Dinas Sosial",
            "Kepala Dinas Pariwisata", "Kepala Dinas Perhubungan", "Sekretaris Daerah",
            "Asisten Sekretaris Daerah", "Camat", "Lurah", "Kepala Bagian Umum",
            "Kepala Bagian Hukum", "Kepala Bagian Keuangan", "Kepala Bidang Anggaran",
            "Kepala Bidang Kepegawaian", "Kepala Bidang Perencanaan",
            "Kepala Bidang Penanaman Modal", "Kepala Sub Bagian Keuangan",
            "Kepala Sub Bagian Umum", "Direktur Rumah Sakit Daerah",
            "Kepala Puskesmas", "Staf Administrasi Pemerintahan", "Staf Keuangan Daerah",
            "Bendahara Daerah", "Sekretaris Dinas"
        ]
        
        # 30% Jabatan Swasta & Akademik (Untuk adversarial OOV Entities)
        jabatan_swasta_akademik = [
            "Direktur Utama", "Manajer Operasional", "Project Manager",
            "HR Manager", "Kepala Cabang", "Supervisor Produksi",
            "Dosen Teknik Informatika", "Kepala Sekolah", "Software Engineer",
            "Data Analyst", "Account Executive", "Marketing Director"
        ]
        
        self.jabatan_list = jabatan_pemerintah + jabatan_swasta_akademik
        
        # Daftar lokasi (kota dan provinsi)
        self.lokasi_list = [
            "Jakarta", "Bandung", "Surabaya", "Yogyakarta",
            "Semarang", "Medan", "Makassar", "Depok", "Bogor",
            "Tangerang", "Bekasi", "Palembang", "Denpasar", "Malang",
            "Padang", "Pekanbaru", "Banjarmasin", "Pontianak", "Manado",
            "Aceh", "Riau", "Lampung", "Bali", "Papua",
            "Jawa Barat", "Jawa Tengah", "Jawa Timur", "Sumatera Utara",
            "Kalimantan Selatan", "Sulawesi Selatan", "Banten",
            "Sumatera Barat", "Kalimantan Timur", "Sulawesi Utara"
        ]
        
        # Phone prefix valid Indonesia
        self.phone_prefixes = [
            '0811', '0812', '0813', '0821', '0822', '0823', # Telkomsel
            '0851', '0852', '0853',                         # Telkomsel (AS/Halo)
            '0855', '0856', '0857', '0858',                 # Indosat
            '0817', '0818', '0819', '0859', '0877', '0878', # XL/Axis
            '0814', '0815', '0816',                         # Indosat lama
            '0895', '0896', '0897', '0898', '0899',         # Tri
            '0831', '0832', '0833', '0838'                  # Axis tambahan
        ]
    
    def generate_nik(self):
        return _generate_nik_valid()
    
    def generate_phone(self):
        """Generate nomor HP Indonesia (format 08xx atau +62xx, total 10-13 digit)"""
        prefix = random.choice(self.phone_prefixes)
        
        # Aturan baku panjang nomor HP Indonesia adalah 10 hingga 13 digit
        target_length = random.randint(10, 13)
        suffix_length = target_length - len(prefix)
        
        suffix = ''.join([str(random.randint(0, 9)) for _ in range(suffix_length)])
        
        if random.random() < 0.3:
            # Format internasional +62 (menggantikan 0 di depan)
            return f"+62{prefix[1:]}{suffix}"
        
        # Format lokal 08xx
        return f"{prefix}{suffix}"
    
    def generate_pii_set(self):
        """Generate satu set PII lengkap"""
        return {
            'nik': self.generate_nik(),
            'nama': fake.name(),
            'telepon': self.generate_phone(),
            'jabatan': random.choice(self.jabatan_list),
            'lokasi': random.choice(self.lokasi_list)
        }
    
    def generate_json_payload(self):
        """
        Format JSON dengan 4 variasi struktur.
        SEMUA template lengkap (5 entity) untuk konsistensi training.
        """
        pii = self.generate_pii_set()
        
        templates = [
            # Template 1: Flat Indonesian
            {
                "nik": pii['nik'],
                "nama": pii['nama'],
                "telepon": pii['telepon'],
                "jabatan": pii['jabatan'],
                "kota": pii['lokasi']
            },
            # Template 2: Nested
            {
                "user": {
                    "id": pii['nik'],
                    "fullName": pii['nama'],
                    "phone": pii['telepon']
                },
                "position": pii['jabatan'],
                "location": pii['lokasi']
            },
            # Template 3: Flat English
            {
                "identity_number": pii['nik'],
                "full_name": pii['nama'],
                "phone_number": pii['telepon'],
                "job_title": pii['jabatan'],
                "city": pii['lokasi']
            },
            # Template 4: Deep nested
            {
                "data": {
                    "personal": {
                        "name": pii['nama'],
                        "nik": pii['nik']
                    },
                    "contact": pii['telepon'],
                    "work": {
                        "position": pii['jabatan'],
                        "office_location": pii['lokasi']
                    }
                }
            }
        ]
        
        template = random.choice(templates)
        payload = json.dumps(template, ensure_ascii=False)
        
        return {
            'payload': payload,
            'format': 'json',
            'pii_data': pii  # Semua entity ada di payload
        }
    
    def generate_formdata_payload(self):
        """
        Format URL-encoded form data dengan 6 variasi.
        SEMUA template lengkap (5 entity) untuk konsistensi.
        Variasi terletak pada nama field (id/nik/identitas, dll).
        """
        pii = self.generate_pii_set()
        nama_enc = quote(pii['nama'])
        jabatan_enc = quote(pii['jabatan'])
        lokasi_enc = quote(pii['lokasi'])
        
        templates = [
            # Template 1: Indonesian standard
            f"nik={pii['nik']}&nama={nama_enc}&telepon={pii['telepon']}&jabatan={jabatan_enc}&kota={lokasi_enc}",
            
            # Template 2: Indonesian formal
            f"nomor_induk={pii['nik']}&nama_lengkap={nama_enc}&nomor_hp={pii['telepon']}&posisi={jabatan_enc}&wilayah={lokasi_enc}",
            
            # Template 3: English snake_case
            f"id={pii['nik']}&name={nama_enc}&phone={pii['telepon']}&position={jabatan_enc}&location={lokasi_enc}",
            
            # Template 4: Mixed
            f"identitas={pii['nik']}&fullname={nama_enc}&kontak={pii['telepon']}&jabatan={jabatan_enc}&lokasi={lokasi_enc}",
            
            # Template 5: Short field names
            f"nik={pii['nik']}&nm={nama_enc}&hp={pii['telepon']}&jab={jabatan_enc}&kt={lokasi_enc}",
            
            # Template 6: Different order
            f"nama={nama_enc}&nik={pii['nik']}&jabatan={jabatan_enc}&kota={lokasi_enc}&telepon={pii['telepon']}"
        ]
        
        template = random.choice(templates)
        
        return {
            'payload': template,
            'format': 'formdata',
            'pii_data': pii  # Semua entity ada di payload
        }
    
    def generate_narrative_payload(self):
        """Format teks naratif berbahasa Indonesia (semua 5 entity)"""
        pii = self.generate_pii_set()
        
        templates = [
            f"Permohonan akses untuk {pii['nama']} dengan NIK {pii['nik']} sebagai {pii['jabatan']} di {pii['lokasi']}. Kontak: {pii['telepon']}",
            f"Data pegawai: {pii['nama']}, NIK {pii['nik']}, menjabat sebagai {pii['jabatan']} di wilayah {pii['lokasi']}, telepon {pii['telepon']}",
            f"{pii['nama']} ({pii['nik']}) mengajukan izin cuti. Jabatan: {pii['jabatan']}, Lokasi: {pii['lokasi']}, HP: {pii['telepon']}",
            f"Surat keterangan untuk {pii['nama']} dengan nomor identitas {pii['nik']} yang bertugas di {pii['lokasi']} sebagai {pii['jabatan']}. Nomor kontak: {pii['telepon']}",
            f"Berdasarkan data pegawai, {pii['nama']} dengan NIK {pii['nik']} ditugaskan di {pii['lokasi']} dengan jabatan {pii['jabatan']}. Nomor HP: {pii['telepon']}",
            f"Yang bertanda tangan di bawah ini, {pii['nama']}, NIK {pii['nik']}, {pii['jabatan']} di {pii['lokasi']}, dengan ini menyatakan. Kontak: {pii['telepon']}",
            f"Mohon diverifikasi data berikut: Nama {pii['nama']}, NIK {pii['nik']}, Jabatan {pii['jabatan']}, Wilayah {pii['lokasi']}, Telepon {pii['telepon']}"
        ]
        
        return {
            'payload': random.choice(templates),
            'format': 'narrative',
            'pii_data': pii
        }
    
    def generate_negative_sample(self):
        """Sample tanpa PII (Negatif) dengan multi-format untuk mencegah bias JSON=PII"""
        format_type = random.choice(['json', 'formdata', 'narrative'])
        
        if format_type == 'json':
            templates = [
                json.dumps({"status": "success", "message": "Sistem diperbarui", "code": 200}),
                json.dumps({"server_uptime": "99.9%", "active_users": random.randint(1000, 5000)}),
                json.dumps({"config": {"firewall": "updated", "port": 8080}}),
                json.dumps({"transaction_summary": {"total_sales": 5000000, "currency": "IDR"}})
            ]
        elif format_type == 'formdata':
            templates = [
                f"action=update&status=success&timestamp={random.randint(1600000000, 1700000000)}",
                "setting=network&firewall=enabled&port=443",
                f"query=dashboard&metrics=users&count={random.randint(100, 999)}"
            ]
        else:
            templates = [
                "Sistem berhasil diperbarui pada tanggal 15 Januari 2026",
                "Rapat koordinasi akan dilaksanakan di ruang meeting lantai 3",
                "Status server: online. Uptime: 99.9%",
                "Backup database selesai pada pukul 03:00 dini hari",
                "Konfigurasi firewall telah diperbarui dengan kebijakan terbaru"
            ]
        
        return {
            'payload': random.choice(templates),
            'format': format_type, # Label as the actual format (JSON/Form/Naratif)
            'pii_data': None
        }
    
    def generate_dataset(self, n_samples=10000):
        """Generate dataset sesuai distribusi proposal"""
        print(f"\n📊 Generating {n_samples} synthetic samples...\n")
        
        # Distribusi: 40% JSON, 40% Form, 15% Narrative, 5% Negative
        n_json = int(n_samples * 0.40)
        n_form = int(n_samples * 0.40)
        n_narrative = int(n_samples * 0.15)
        n_negative = n_samples - n_json - n_form - n_narrative
        
        print(f"   📌 JSON payloads     : {n_json:>5}")
        print(f"   📌 Form-Data payloads: {n_form:>5}")
        print(f"   📌 Narrative payloads: {n_narrative:>5}")
        print(f"   📌 Negative samples  : {n_negative:>5}")
        print()
        
        data = []
        
        for _ in tqdm(range(n_json), desc="JSON      "):
            data.append(self.generate_json_payload())
        for _ in tqdm(range(n_form), desc="Form-Data "):
            data.append(self.generate_formdata_payload())
        for _ in tqdm(range(n_narrative), desc="Narrative "):
            data.append(self.generate_narrative_payload())
        for _ in tqdm(range(n_negative), desc="Negative  "):
            data.append(self.generate_negative_sample())
        
        df = pd.DataFrame(data)
        df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
        return df


# ... (kode lainnya tetap sama)

def main():
    print("="*65)
    print("  📦 DATA GENERATOR (Contextual Data Synthesis)")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*65)
    
    generator = PiiDataGenerator()
    df = generator.generate_dataset(n_samples=10000)
    
    # Save
    os.makedirs('data/raw', exist_ok=True)
    pkl_path = 'data/raw/dataset_raw.pkl'
    csv_path = 'data/raw/dataset_raw.csv'
    
    df.to_pickle(pkl_path)
    
    df_csv = df.copy()
    df_csv['pii_data'] = df_csv['pii_data'].apply(
        lambda x: json.dumps(x, ensure_ascii=False) if x else None
    )
    df_csv.to_csv(csv_path, index=False, encoding='utf-8')
    
    # Statistics
    print("\n" + "="*65)
    print("  📈 DATASET STATISTICS")
    print("="*65)
    print(f"  Total samples: {len(df)}")
    print(f"\n  Distribusi format:")
    for fmt, count in df['format'].value_counts().sort_index().items():
        pct = (count/len(df))*100
        print(f"     {fmt:<12} : {count:>5} ({pct:>4.1f}%)")
    
    print(f"\n  Contoh data per format:")
    print("  " + "-"*61)
    
    # PERBAIKAN: Menggunakan .unique() agar dinamis dan aman
    for fmt in df['format'].unique():
        # Menggunakan .head(1) lebih aman daripada .iloc[0] jika data kosong
        sample = df[df['format'] == fmt].head(1)
        if not sample.empty:
            payload = sample.iloc[0]['payload']
            preview = payload[:130]
            print(f"\n  [{fmt.upper()}]")
            print(f"  {preview}{'...' if len(payload) > 130 else ''}")
    
    print(f"\n  ✅ Saved: {pkl_path}")
    print(f"  ✅ Saved: {csv_path}")
    print("="*65)

if __name__ == "__main__":
    main()