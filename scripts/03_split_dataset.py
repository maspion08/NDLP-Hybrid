"""
Stratified Dataset Split (80:10:10)
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Sesuai Bab III.3.c.1 Proposal:
- 80% training (8.000)
- 10% validation (1.000)
- 10% test (1.000)
- Stratified by format (preserve distribution)
- Reproducible (seed=42)
"""
import os
import pandas as pd
from sklearn.model_selection import train_test_split


SEED = 42


def stratified_split(df, train_size=0.8, val_size=0.1, test_size=0.1):
    """Split with stratification by 'format' column"""
    assert abs(train_size + val_size + test_size - 1.0) < 1e-6, "Sizes must sum to 1.0"
    
    # First split: train vs (val+test)
    df_train, df_temp = train_test_split(
        df,
        test_size=(val_size + test_size),
        stratify=df['format'],
        random_state=SEED
    )
    
    # Second split: val vs test
    val_ratio = val_size / (val_size + test_size)
    df_val, df_test = train_test_split(
        df_temp,
        test_size=(1 - val_ratio),
        stratify=df_temp['format'],
        random_state=SEED
    )
    
    # Reset indices
    df_train = df_train.reset_index(drop=True)
    df_val = df_val.reset_index(drop=True)
    df_test = df_test.reset_index(drop=True)
    
    return df_train, df_val, df_test


def print_distribution(df, name):
    """Print format distribution"""
    print(f"\n  {name} ({len(df)} samples):")
    for fmt, count in df['format'].value_counts().sort_index().items():
        pct = (count/len(df))*100
        print(f"     {fmt:<12} : {count:>5} ({pct:>4.1f}%)")


def main():
    print("="*65)
    print("  ✂️  DATASET SPLIT (Stratified 80:10:10)")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*65)
    
    input_path = 'data/processed/dataset_bio.pkl'
    if not os.path.exists(input_path):
        print(f"❌ File not found: {input_path}")
        print("   Run: python scripts\\02_bio_tagger.py first")
        return
    
    print(f"\n📂 Loading: {input_path}")
    df = pd.read_pickle(input_path)
    print(f"   {len(df)} total samples")
    
    # Split
    df_train, df_val, df_test = stratified_split(df)
    
    # Save
    os.makedirs('data/processed', exist_ok=True)
    df_train.to_pickle('data/processed/train.pkl')
    df_val.to_pickle('data/processed/val.pkl')
    df_test.to_pickle('data/processed/test.pkl')
    
    print("\n" + "="*65)
    print("  📊 SPLIT DISTRIBUTION")
    print("="*65)
    
    print_distribution(df_train, "TRAIN (80%)")
    print_distribution(df_val,   "VAL   (10%)")
    print_distribution(df_test,  "TEST  (10%)")
    
    print("\n" + "="*65)
    print("  ✅ Saved files:")
    print("="*65)
    print(f"     data/processed/train.pkl  ({len(df_train):>5} samples)")
    print(f"     data/processed/val.pkl    ({len(df_val):>5} samples)")
    print(f"     data/processed/test.pkl   ({len(df_test):>5} samples)")
    print("="*65)


if __name__ == "__main__":
    main()