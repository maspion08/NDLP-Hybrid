"""
Combine Training Dataset + Adversarial Samples
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Menggabungkan:
- 10.000 sampel sintetis (training distribution)
- 1.000 adversarial samples (data augmentation)
- Total: 11.000 untuk train/val/test split

Adversarial samples digunakan sebagai data augmentation untuk meningkatkan
robustness model terhadap edge cases dan out-of-distribution inputs.

LANDASAN ILMIAH:
- Adversarial training (Goodfellow et al., 2014)
- Data augmentation untuk NER (Wei & Zou, 2019)
- BigCode PII Dataset (2023): adversarial samples for PII robustness
"""
import os
import sys
import json
import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from importlib import import_module
bio_module = import_module('02_bio_tagger')

SEED = 42


def main():
    print("="*70)
    print("  🔀 COMBINE TRAINING + ADVERSARIAL DATASET")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*70)
    
    # Load existing datasets
    print("\n📂 Loading datasets...")
    
    # 1. Load original 10K samples
    main_path = 'data/raw/dataset_raw.pkl'
    df_main = pd.read_pickle(main_path)
    df_main['source'] = 'main'
    print(f"   Main dataset: {len(df_main)} samples")
    
    # 2. Load adversarial 1K samples
    adv_path = 'data/raw/adversarial.pkl'
    df_adv = pd.read_pickle(adv_path)
    print(f"   Adversarial:  {len(df_adv)} samples")
    
    # 3. Combine
    df_combined = pd.concat([df_main, df_adv], ignore_index=True)
    print(f"\n   Combined:     {len(df_combined)} samples")
    
    # Shuffle
    df_combined = df_combined.sample(frac=1, random_state=SEED).reset_index(drop=True)
    
    # Save combined raw
    print("\n💾 Saving combined raw dataset...")
    os.makedirs('data/raw', exist_ok=True)
    combined_pkl = 'data/raw/dataset_combined.pkl'
    df_combined.to_pickle(combined_pkl)
    print(f"   ✅ Saved: {combined_pkl}")
    
    # === BIO Tagging on combined dataset ===
    print("\n🏷️  Running BIO tagging on combined dataset...")
    tagger = bio_module.BioTagger()
    df_tagged = tagger.process_dataset(df_combined)
    
    # Add source column from original (preserve traceability)
    df_tagged['source'] = df_combined['source'].values
    
    # Save tagged combined
    tagged_pkl = 'data/processed/dataset_combined_bio.pkl'
    os.makedirs('data/processed', exist_ok=True)
    df_tagged.to_pickle(tagged_pkl)
    print(f"   ✅ Saved: {tagged_pkl}")
    
    # === Stratified Split 80:10:10 ===
    print("\n✂️  Splitting 80:10:10 (stratified by format)...")
    
    df_train, df_temp = train_test_split(
        df_tagged,
        test_size=0.2,
        stratify=df_tagged['format'],
        random_state=SEED
    )
    
    df_val, df_test = train_test_split(
        df_temp,
        test_size=0.5,
        stratify=df_temp['format'],
        random_state=SEED
    )
    
    df_train = df_train.reset_index(drop=True)
    df_val = df_val.reset_index(drop=True)
    df_test = df_test.reset_index(drop=True)
    
    # Save splits (overwrite existing)
    df_train.to_pickle('data/processed/train.pkl')
    df_val.to_pickle('data/processed/val.pkl')
    df_test.to_pickle('data/processed/test.pkl')
    
    # === Statistics ===
    print("\n" + "="*70)
    print("  📈 ENRICHED DATASET STATISTICS")
    print("="*70)
    print(f"  Total samples: {len(df_tagged):,}")
    print(f"\n  Source breakdown:")
    for src, count in df_tagged['source'].value_counts().items():
        pct = (count/len(df_tagged))*100
        print(f"     {src:<15} : {count:>5} ({pct:>4.1f}%)")
    
    print(f"\n  Format distribution:")
    for fmt, count in df_tagged['format'].value_counts().sort_index().items():
        pct = (count/len(df_tagged))*100
        print(f"     {fmt:<15} : {count:>5} ({pct:>4.1f}%)")
    
    print(f"\n  Split distribution:")
    print(f"     Train  : {len(df_train):>5} ({len(df_train)/len(df_tagged)*100:.1f}%)")
    print(f"     Val    : {len(df_val):>5} ({len(df_val)/len(df_tagged)*100:.1f}%)")
    print(f"     Test   : {len(df_test):>5} ({len(df_test)/len(df_tagged)*100:.1f}%)")
    
    # Verify stratification
    print(f"\n  Per-format split verification:")
    print("  " + "-"*60)
    print(f"  {'Format':<15} {'Train':>8} {'Val':>8} {'Test':>8}")
    for fmt in sorted(df_tagged['format'].unique()):
        n_train = (df_train['format'] == fmt).sum()
        n_val = (df_val['format'] == fmt).sum()
        n_test = (df_test['format'] == fmt).sum()
        print(f"  {fmt:<15} {n_train:>8} {n_val:>8} {n_test:>8}")
    
    # BIO statistics
    print(f"\n  Label statistics (combined):")
    label_counts = tagger.get_statistics(df_tagged)
    total_tokens = sum(label_counts.values())
    print(f"     Total tokens: {total_tokens:,}")
    for label in sorted(label_counts.keys()):
        count = label_counts[label]
        pct = (count/total_tokens)*100
        print(f"     {label:<12} : {count:>7,} ({pct:>5.2f}%)")
    
    print(f"\n  ✅ Files saved:")
    print(f"     data/raw/dataset_combined.pkl ({len(df_combined):,} samples)")
    print(f"     data/processed/dataset_combined_bio.pkl ({len(df_tagged):,} samples)")
    print(f"     data/processed/train.pkl ({len(df_train):,} samples) [OVERWRITTEN]")
    print(f"     data/processed/val.pkl   ({len(df_val):,} samples) [OVERWRITTEN]")
    print(f"     data/processed/test.pkl  ({len(df_test):,} samples) [OVERWRITTEN]")
    print("="*70)


if __name__ == "__main__":
    main()