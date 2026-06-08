"""
BIO Tagger untuk Held-Out Test Set
Tugas Akhir: Arga Ariyuda Avian (2221101774)

BIO tag naturalistic dataset menggunakan ground truth dari pii_data.
Menggunakan tokenizer dan logic yang sama dengan training data
untuk konsistensi.
"""
import os
import sys
import json
import pandas as pd
from tqdm import tqdm
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import BioTagger from existing script
from importlib import import_module
bio_module = import_module('02_bio_tagger')


def main():
    print("="*70)
    print("  🏷️  BIO TAGGER FOR HELD-OUT TEST SET")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*70)
    
    input_path = 'data/test_holdout/naturalistic.pkl'
    if not os.path.exists(input_path):
        print(f"❌ File not found: {input_path}")
        print("   Run scripts\\17_naturalistic_generator.py first")
        return
    
    print(f"\n📂 Loading: {input_path}")
    df = pd.read_pickle(input_path)
    print(f"   {len(df)} samples loaded")
    
    # Initialize tagger (same as training data)
    tagger = bio_module.BioTagger()
    df_tagged = tagger.process_dataset(df)
    
    # Save
    output_path = 'data/test_holdout/naturalistic_bio.pkl'
    df_tagged.to_pickle(output_path)
    
    # Statistics
    label_counts = tagger.get_statistics(df_tagged)
    total_tokens = sum(label_counts.values())
    
    print("\n" + "="*70)
    print("  📊 BIO TAGGING STATISTICS - Held-Out Set")
    print("="*70)
    print(f"  Total samples: {len(df_tagged)}")
    print(f"  Total tokens: {total_tokens:,}")
    
    print(f"\n  Label distribution:")
    for label in sorted(label_counts.keys()):
        count = label_counts[label]
        pct = (count/total_tokens)*100
        print(f"     {label:<12} : {count:>7,} ({pct:>5.2f}%)")
    
    # Detection coverage per format
    print(f"\n  📊 Detection coverage per format:")
    print("  " + "-"*60)
    for fmt in df_tagged['format'].unique():
        fmt_df = df_tagged[df_tagged['format'] == fmt]
        nik_detected = fmt_df['labels'].apply(lambda x: 'B-NIK' in x).sum()
        phone_detected = fmt_df['labels'].apply(lambda x: 'B-PHONE' in x).sum()
        nama_detected = fmt_df['labels'].apply(lambda x: 'B-NAMA' in x).sum()
        jabatan_detected = fmt_df['labels'].apply(lambda x: 'B-JABATAN' in x).sum()
        lokasi_detected = fmt_df['labels'].apply(lambda x: 'B-LOKASI' in x).sum()
        total = len(fmt_df)
        
        print(f"\n  [{fmt.upper()}]: {total} samples")
        print(f"     NIK    : {nik_detected}/{total} ({nik_detected/total*100:.1f}%)")
        print(f"     PHONE  : {phone_detected}/{total} ({phone_detected/total*100:.1f}%)")
        print(f"     NAMA   : {nama_detected}/{total} ({nama_detected/total*100:.1f}%)")
        print(f"     JABATAN: {jabatan_detected}/{total} ({jabatan_detected/total*100:.1f}%)")
        print(f"     LOKASI : {lokasi_detected}/{total} ({lokasi_detected/total*100:.1f}%)")
    
    # Show sample
    print(f"\n  📝 Sample tagged outputs:")
    print("  " + "-"*60)
    for fmt in ['email_signature', 'database_export', 'json_log']:
        if (df_tagged['format'] == fmt).any():
            sample = df_tagged[df_tagged['format'] == fmt].iloc[0]
            print(f"\n  [{fmt.upper()}]")
            print(f"  Payload: {sample['payload'][:120]}...")
            non_o = [(t, l) for t, l in zip(sample['tokens'], sample['labels']) if l != 'O']
            if non_o:
                print(f"  Entities ({len(non_o)} tokens):")
                for token, label in non_o[:6]:
                    print(f"     '{token}' -> {label}")
    
    print(f"\n  ✅ Saved: {output_path}")
    print("="*70)


if __name__ == "__main__":
    main()