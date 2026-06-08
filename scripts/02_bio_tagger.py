"""
BIO Tagger - Context-Aware Tokenization & Auto-Labeling
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Sesuai Bab III.3.c.1 Proposal:
- Tokenisasi mempertahankan struktur (JSON, form, narrative)
- Pelabelan otomatis BIO standar
- Format: B-{ENTITY}, I-{ENTITY}, O

Entity Types:
- NIK     : 16 digit identity number
- PHONE   : Indonesian phone number
- NAMA    : Full name (multi-token)
- JABATAN : Job title (multi-token)
- LOKASI  : Location (multi-token)
"""
import re
import os
import json
import pandas as pd
from urllib.parse import unquote
from tqdm import tqdm
from collections import Counter


class BioTagger:
    """BIO tagger menggunakan ground truth dari pii_data"""
    
    def __init__(self):
        self.nik_pattern = re.compile(r'\b\d{16}\b')
        self.phone_pattern = re.compile(r'(?:\+62|0)\d{8,12}\b')
    
    def tokenize(self, text):
        """
        Context-aware tokenizer:
        - Phone +62xxx kept as 1 token
        - NIK 16 digit kept as 1 token
        - Latin words (with accents) as tokens
        - Punctuation as separate tokens
        """
        pattern = r'\+62\d{8,12}|\d+|[a-zA-Z\u00C0-\u017F]+|[^\w\s]'
        return re.findall(pattern, text)
    
    def find_token_span(self, tokens, target_text):
        """Find position of target tokens in token list (sliding window)"""
        if not target_text or not tokens:
            return None
        
        target_tokens = self.tokenize(target_text)
        if not target_tokens:
            return None
        
        # Strategy 1: Exact match
        for i in range(len(tokens) - len(target_tokens) + 1):
            if tokens[i:i + len(target_tokens)] == target_tokens:
                return (i, i + len(target_tokens) - 1)
        
        # Strategy 2: Case-insensitive
        target_lower = [t.lower() for t in target_tokens]
        tokens_lower = [t.lower() for t in tokens]
        for i in range(len(tokens_lower) - len(target_lower) + 1):
            if tokens_lower[i:i + len(target_lower)] == target_lower:
                return (i, i + len(target_lower) - 1)
        
        return None
    
    def decode_url_value(self, text):
        """Decode URL-encoded text"""
        try:
            return unquote(text)
        except:
            return text
    
    def tag_sample(self, payload, pii_data, format_type):
        """Tag single sample with BIO labels using ground truth"""
        # URL decode for form-data
        if format_type == 'formdata':
            decoded = self.decode_url_value(payload)
        else:
            decoded = payload
        
        tokens = self.tokenize(decoded)
        labels = ['O'] * len(tokens)
        
        # Negative samples: all O
        if pii_data is None or format_type == 'negative':
            return tokens, labels
        
        # Tag entities (order matters: most specific first)
        entities = [
            ('nik', 'NIK'),
            ('telepon', 'PHONE'),
            ('jabatan', 'JABATAN'),  # Multi-word, before NAMA
            ('lokasi', 'LOKASI'),
            ('nama', 'NAMA')
        ]
        
        for field, label_type in entities:
            if field not in pii_data or not pii_data[field]:
                continue
            
            target = pii_data[field]
            span = self.find_token_span(tokens, target)
            
            if span is not None:
                start, end = span
                # Avoid overwriting existing labels
                if any(labels[i] != 'O' for i in range(start, end + 1)):
                    continue
                
                labels[start] = f'B-{label_type}'
                for i in range(start + 1, end + 1):
                    labels[i] = f'I-{label_type}'
        
        return tokens, labels
    
    def process_dataset(self, df):
        """Process entire dataset with progress bar"""
        results = []
        print(f"\n🔄 Processing {len(df)} samples...")
        
        for _, row in tqdm(df.iterrows(), total=len(df), desc="BIO Tagging"):
            tokens, labels = self.tag_sample(
                payload=row['payload'],
                pii_data=row['pii_data'],
                format_type=row['format']
            )
            results.append({
                'tokens': tokens,
                'labels': labels,
                'format': row['format'],
                'payload': row['payload']
            })
        
        return pd.DataFrame(results)
    
    def get_statistics(self, df_tagged):
        """Compute label distribution"""
        all_labels = []
        for labels in df_tagged['labels']:
            all_labels.extend(labels)
        return Counter(all_labels)


def main():
    print("="*65)
    print("  🏷️  BIO TAGGER (Context-Aware)")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*65)
    
    input_path = 'data/raw/dataset_raw.pkl'
    if not os.path.exists(input_path):
        print(f"❌ File not found: {input_path}")
        print("   Run: python scripts\\01_data_generator.py first")
        return
    
    print(f"\n📂 Loading: {input_path}")
    df = pd.read_pickle(input_path)
    print(f"   {len(df)} samples loaded")
    
    tagger = BioTagger()
    df_tagged = tagger.process_dataset(df)
    
    os.makedirs('data/processed', exist_ok=True)
    output_path = 'data/processed/dataset_bio.pkl'
    df_tagged.to_pickle(output_path)
    
    label_counts = tagger.get_statistics(df_tagged)
    total_tokens = sum(label_counts.values())
    
    print("\n" + "="*65)
    print("  📊 BIO TAGGING STATISTICS")
    print("="*65)
    print(f"  Total samples: {len(df_tagged)}")
    print(f"  Total tokens: {total_tokens:,}")
    
    print(f"\n  Label distribution:")
    for label in sorted(label_counts.keys()):
        count = label_counts[label]
        pct = (count/total_tokens)*100
        print(f"     {label:<12} : {count:>7,} ({pct:>5.2f}%)")
    
    print(f"\n  📝 Sample tagged outputs:")
    print("  " + "-"*61)
    
    for fmt in df_tagged['format'].unique():
        fmt_data = df_tagged[df_tagged['format'] == fmt]
        if not fmt_data.empty:
            sample = fmt_data.iloc[0]
            print(f"\n  [{fmt.upper()}]")
            print(f"  Payload: {sample['payload'][:90]}...")
            
            non_o = [(t, l) for t, l in zip(sample['tokens'], sample['labels']) if l != 'O']
            if non_o:
                print(f"  Entities ({len(non_o)} tokens):")
                for token, label in non_o[:8]:
                    print(f"     '{token}' -> {label}")
    
    print(f"\n  ✅ Saved: {output_path}")
    print("="*65)


if __name__ == "__main__":
    main()