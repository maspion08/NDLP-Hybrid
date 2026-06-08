"""
Manual Inspection & Cross-Validation
Tugas Akhir: Arga Ariyuda Avian (2221101774)
"""
import pandas as pd


def inspect():
    print("="*65)
    print("  🔬 DATASET MANUAL INSPECTION")
    print("="*65)
    
    df = pd.read_pickle('data/processed/dataset_bio.pkl')
    raw_df = pd.read_pickle('data/raw/dataset_raw.pkl')
    
    print(f"\n  📊 Total: {len(df)} samples, {sum(len(t) for t in df['tokens']):,} tokens")
    
    # Per-format stats
    print(f"\n  📈 Per-Format Statistics:")
    print("  " + "-"*61)
    for fmt in df['format'].unique():
        sub = df[df['format'] == fmt]
        avg = sub['tokens'].apply(len).mean()
        mn = sub['tokens'].apply(len).min()
        mx = sub['tokens'].apply(len).max()
        
        all_lbl = []
        for labels in sub['labels']:
            all_lbl.extend([l for l in labels if l != 'O'])
        
        unique = len(set(all_lbl))
        print(f"\n  [{fmt.upper()}] {len(sub)} samples")
        print(f"    Tokens     : avg={avg:.1f}, min={mn}, max={mx}")
        print(f"    Entity types: {unique}")
    
    # Sample inspection
    print(f"\n\n  📝 SAMPLE OUTPUTS:")
    print("="*65)
    
    for fmt in ['json', 'formdata', 'narrative', 'negative']:
        sample = df[df['format'] == fmt].sample(1, random_state=42).iloc[0]
        print(f"\n[{fmt.upper()}]")
        print(f"Payload: {sample['payload'][:130]}...")
        
        # Group consecutive entities
        entities = []
        current_type = None
        current_tokens = []
        
        for token, label in zip(sample['tokens'], sample['labels']):
            if label.startswith('B-'):
                if current_type:
                    entities.append((current_type, ' '.join(current_tokens)))
                current_type = label[2:]
                current_tokens = [token]
            elif label.startswith('I-'):
                current_tokens.append(token)
            else:
                if current_type:
                    entities.append((current_type, ' '.join(current_tokens)))
                    current_type = None
                    current_tokens = []
        
        if current_type:
            entities.append((current_type, ' '.join(current_tokens)))
        
        if entities:
            print(f"Entities:")
            for ent, val in entities:
                print(f"   {ent:<10} : {val}")
        else:
            print(f"   No entities (correct for negative)")
    
    # Cross-validation
    print(f"\n\n  🔍 CROSS-VALIDATION (100 random samples):")
    print("="*65)
    
    mismatches = 0
    sample_indices = raw_df.sample(100, random_state=42).index
    
    for idx in sample_indices:
        raw_row = raw_df.loc[idx]
        bio_row = df.iloc[idx]
        
        if raw_row['pii_data'] is None:
            continue
        
        # Check NIK
        for token, label in zip(bio_row['tokens'], bio_row['labels']):
            if label == 'B-NIK':
                if token != raw_row['pii_data']['nik']:
                    mismatches += 1
                break
    
    if mismatches == 0:
        print(f"  ✅ Ground truth perfectly matches BIO labels (0 mismatches)")
    else:
        print(f"  ⚠️  {mismatches} mismatches found")
    
    print("\n" + "="*65)
    print("  ✅ Inspection completed")
    print("="*65)


if __name__ == "__main__":
    inspect()