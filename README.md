\# NDLP Hybrid — Network Data Leakage Prevention



\*\*Tugas Akhir\*\*

Arga Ariyuda Avian (2221101774)

Politeknik Siber dan Sandi Negara

Pembimbing: Tiyas Yulita, M.Si.



\---



\## Deskripsi



Sistem Network Data Leakage Prevention (NDLP) berbasis

Transparent Proxy dengan metode hibrida Rule-Based dan

Machine Learning (Hybrid CRF) untuk mendeteksi dan

melakukan masking entitas data kependudukan Indonesia

pada lalu lintas HTTPS.



\*\*Entitas yang dideteksi:\*\*

\- NIK (Nomor Induk Kependudukan)

\- Nomor Telepon

\- Nama Lengkap

\- Jabatan

\- Lokasi/Wilayah



\---



\## Struktur Repository

NDLP-Hybrid/
├── README.md
├── requirements.txt
├── .gitignore
├── nik_validation/              # Eksperimen validasi struktural NIK
│   ├── generate_nik_valid.py
│   ├── inject_and_test.py
│   ├── analyze_log_v2.py
│   ├── payloads.json
│   ├── nik_valid_100.{csv,json,txt}
│   └── run_test.sh
└── scripts/                     # Pipeline utama (dieksekusi berurutan)
    ├── 01_data_generator.py         # Pembangkitan dataset sintetis
    ├── 02_bio_tagger.py             # Pelabelan BIO tagging otomatis
    ├── 03_split_dataset.py         # Stratified split 80:10:10
    ├── 04_validate.py
    ├── 07_features_v2.py            # Ekstraksi 47 fitur Hybrid CRF
    ├── 08_evaluator.py
    ├── 10_train_regex.py … 13_train_hybrid_hmm.py   # Training 4 model non-CRF
    ├── 15_adversarial_generator.py
    ├── 17_naturalistic_generator.py # Pembangkit held-out naturalistic set
    ├── 18_tag_holdout.py … 23_test_hard_adversarial.py
    ├── 25_build_gazetteer.py
    ├── 26_train_hybrid_crf_v2.py    # Training model final Hybrid CRF
    ├── 27_evaluate_crf_v2.py        # Evaluasi model final
    ├── 28_prepare_inter_annotation_v3.py  # Persiapan anotasi Cohen's Kappa
    ├── 31_compute_inter_kappa.py    # Perhitungan Cohen's Kappa
    ├── 33_mcnemars_test.py          # Uji signifikansi McNemar
    └── nik_utils.py


\## Cara Menjalankan



\### 1. Persiapan Environment



```bash

python -m venv venv

\# Windows:

venv\\Scripts\\activate

\# Linux/Mac:

source venv/bin/activate



pip install -r requirements.txt

```



\### 2. Generate Dataset



```bash

python scripts/01\_data\_generator.py

```



\### 3. BIO Tagging



```bash

python scripts/02\_bio\_tagger.py

```



\### 4. Training Model



```bash

\# Training semua 5 model

python scripts/10\_train\_regex.py

python scripts/11\_train\_hmm.py

python scripts/12\_train\_crf.py

python scripts/13\_train\_hybrid\_hmm.py

python scripts/14\_train\_hybrid\_crf.py

```



\### 5. Evaluasi



```bash

python scripts/20\_evaluate\_all.py

```



\### 6. Deployment (di VM\_Proxy dengan mitmproxy)



```bash

mitmdump -s ndlp\_addon.py --mode transparent \\

&#x20;   --listen-host 0.0.0.0 --listen-port 8080 --ssl-insecure

```



\---



\## Topologi Testbed (GNS3)

VM\_Client (192.168.1.10)

↓ HTTPS request

VM\_Proxy (192.168.1.1) ← mitmproxy + Hybrid CRF

↓ Masked payload

VM\_Nginx (192.168.2.10)



\---



\## Hasil Utama



| Model | F1 Test Set | F1 Held-Out | Gap |

|-------|-------------|-------------|-----|

| Regex Murni | 0,3990 | 0,3972 | 0,0018 |

| HMM Murni | 0,5980 | 0,3839 | 0,2141 |

| CRF Murni | 0,9996 | 0,8124 | 0,1872 |

| Hybrid HMM | 0,9751 | 0,6930 | 0,2821 |

| \*\*Hybrid CRF\*\* | \*\*0,9998\*\* | \*\*0,9273\*\* | \*\*0,0725\*\* |



\---



\## Referensi



\- UU PDP No. 27/2022

\- Permendagri No. 137/2017 (Kode Wilayah NIK)

\- Lafferty et al. (2001) — Conditional Random Fields

\- Privacy by Design, Cavoukian (2009)







