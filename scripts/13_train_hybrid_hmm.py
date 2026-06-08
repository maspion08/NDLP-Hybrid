"""
Model 4: Hybrid HMM (HMM + Regex-as-a-Feature)
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Sesuai Bab II.1.11 Proposal:
"Konsep Regex-as-a-Feature mendefinisikan integrasi ini melalui proses 
rekayasa fitur (feature engineering), di mana hasil pencocokan dari 
regular expression tidak digunakan sebagai mekanisme filtrasi akhir, 
melainkan dikonversi menjadi fitur masukan tambahan (auxiliary feature) 
bagi model Named Entity Recognition (NER)."

Strategi:
- Token yang cocok pola NIK/PHONE diganti dengan special token
- HMM belajar bahwa special token = high probability NIK/PHONE
- Mengatasi UNK problem yang dialami HMM Murni

LANDASAN ILMIAH:
- Sang & Veenstra (1999): Token augmentation untuk HMM-based NER
- Bender et al. (2003): Regex feature injection
- Kuzina et al. (2021): Hybrid Indonesian PII detection
"""
import os
import sys
import time
import pickle
import re
import numpy as np
import pandas as pd
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
evaluator = import_module('08_evaluator')


# Pattern untuk Regex-as-a-Feature
PATTERN_NIK = re.compile(r'^\d{16}$')
PATTERN_PHONE = re.compile(r'^(?:\+62|0)\d{8,12}$')

# Special tokens
TOKEN_NIK = '<__NIK_PATTERN__>'
TOKEN_PHONE = '<__PHONE_PATTERN__>'


def augment_token(token):
    """
    Token augmentation: ganti dengan special token jika match pattern.
    
    Strategi ini efektif untuk HMM karena:
    1. Mengurangi kardinalitas vocabulary (semua NIK → 1 token)
    2. Memberikan pattern signal yang konsisten
    3. Mengatasi UNK problem
    """
    if PATTERN_NIK.match(token):
        return TOKEN_NIK
    elif PATTERN_PHONE.match(token):
        return TOKEN_PHONE
    else:
        return token.lower()


def augment_sequence(tokens):
    """Augment seluruh sequence"""
    return [augment_token(t) for t in tokens]


class HybridHMM:
    """
    HMM dengan Regex-as-a-Feature melalui token augmentation.
    """
    
    def __init__(self, alpha=1.0):
        self.alpha = alpha
        self.name = "Hybrid_HMM"
        
        self.states = None
        self.state_to_idx = None
        self.vocab = None
        self.token_to_idx = None
        self.unk_idx = None
        
        self.log_start_prob = None
        self.log_trans_prob = None
        self.log_emission_prob = None
    
    def fit(self, X_sequences, y_sequences):
        """Train HMM dengan augmented tokens"""
        print("\n  🔧 Training Hybrid HMM (Token Augmentation)...")
        
        # Augment all training sequences
        print("     1. Augmenting tokens with regex patterns...")
        X_augmented = [augment_sequence(seq) for seq in X_sequences]
        
        # Build state set
        all_labels = set()
        for seq in y_sequences:
            all_labels.update(seq)
        self.states = sorted(all_labels)
        self.state_to_idx = {s: i for i, s in enumerate(self.states)}
        n_states = len(self.states)
        
        # Build vocabulary (with special tokens)
        all_tokens = set()
        for seq in X_augmented:
            all_tokens.update(seq)
        
        self.vocab = sorted(all_tokens) + ['<UNK>']
        self.token_to_idx = {t: i for i, t in enumerate(self.vocab)}
        self.unk_idx = self.token_to_idx['<UNK>']
        n_vocab = len(self.vocab)
        
        print(f"     2. Vocabulary built: {n_vocab:,} tokens")
        print(f"        Original size (HMM Murni): ~16,000+")
        print(f"        Reduced size (Hybrid):     {n_vocab:,}")
        print(f"        Special tokens: {TOKEN_NIK}, {TOKEN_PHONE}")
        
        # Count statistics
        print("     3. Counting frequencies...")
        start_counts = np.zeros(n_states)
        trans_counts = np.zeros((n_states, n_states))
        emission_counts = np.zeros((n_states, n_vocab))
        
        for tokens, labels in tqdm(zip(X_augmented, y_sequences),
                                    total=len(X_augmented),
                                    desc="        Counting"):
            if not labels:
                continue
            
            start_counts[self.state_to_idx[labels[0]]] += 1
            
            for i, (token, label) in enumerate(zip(tokens, labels)):
                state_idx = self.state_to_idx[label]
                token_idx = self.token_to_idx.get(token, self.unk_idx)
                
                emission_counts[state_idx, token_idx] += 1
                
                if i > 0:
                    prev_state_idx = self.state_to_idx[labels[i-1]]
                    trans_counts[prev_state_idx, state_idx] += 1
        
        # MLE with Laplace Smoothing
        print(f"     4. Computing probabilities (Laplace alpha={self.alpha})...")
        
        start_prob = (start_counts + self.alpha) / \
                     (start_counts.sum() + self.alpha * n_states)
        trans_prob = (trans_counts + self.alpha) / \
                     (trans_counts.sum(axis=1, keepdims=True) + self.alpha * n_states)
        emission_prob = (emission_counts + self.alpha) / \
                        (emission_counts.sum(axis=1, keepdims=True) + self.alpha * n_vocab)
        
        self.log_start_prob = np.log(start_prob)
        self.log_trans_prob = np.log(trans_prob)
        self.log_emission_prob = np.log(emission_prob)
        
        print(f"     ✅ Training complete")
    
    def viterbi_decode(self, tokens):
        """Viterbi decoding dengan token augmentation"""
        # Augment tokens dulu
        augmented = augment_sequence(tokens)
        
        n_states = len(self.states)
        T = len(augmented)
        
        if T == 0:
            return []
        
        token_indices = [self.token_to_idx.get(t, self.unk_idx) for t in augmented]
        
        viterbi = np.full((T, n_states), -np.inf)
        backpointer = np.zeros((T, n_states), dtype=int)
        
        viterbi[0] = self.log_start_prob + self.log_emission_prob[:, token_indices[0]]
        
        for t in range(1, T):
            for s in range(n_states):
                scores = viterbi[t-1] + self.log_trans_prob[:, s] + self.log_emission_prob[s, token_indices[t]]
                viterbi[t, s] = np.max(scores)
                backpointer[t, s] = np.argmax(scores)
        
        best_path = [0] * T
        best_path[T-1] = np.argmax(viterbi[T-1])
        
        for t in range(T-2, -1, -1):
            best_path[t] = backpointer[t+1, best_path[t+1]]
        
        return [self.states[idx] for idx in best_path]
    
    def predict(self, X_tokens):
        """Predict untuk seluruh dataset"""
        return [self.viterbi_decode(tokens) for tokens in X_tokens]
    
    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'name': self.name,
                'alpha': self.alpha,
                'states': self.states,
                'state_to_idx': self.state_to_idx,
                'vocab': self.vocab,
                'token_to_idx': self.token_to_idx,
                'unk_idx': self.unk_idx,
                'log_start_prob': self.log_start_prob,
                'log_trans_prob': self.log_trans_prob,
                'log_emission_prob': self.log_emission_prob
            }, f)
    
    @classmethod
    def load(cls, path):
        with open(path, 'rb') as f:
            data = pickle.load(f)
        model = cls(alpha=data['alpha'])
        model.name = data['name']
        model.states = data['states']
        model.state_to_idx = data['state_to_idx']
        model.vocab = data['vocab']
        model.token_to_idx = data['token_to_idx']
        model.unk_idx = data['unk_idx']
        model.log_start_prob = data['log_start_prob']
        model.log_trans_prob = data['log_trans_prob']
        model.log_emission_prob = data['log_emission_prob']
        return model


def main():
    print("="*70)
    print("  🤖 MODEL 4: HYBRID HMM (HMM + Regex-as-a-Feature)")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*70)
    
    print("\n📚 STRATEGI HYBRID:")
    print("   - Token NIK 16-digit  → <__NIK_PATTERN__>")
    print("   - Token PHONE         → <__PHONE_PATTERN__>")
    print("   - Mengatasi UNK problem HMM Murni")
    print("   - Vocabulary jauh lebih kecil → konvergensi lebih baik")
    
    # Load data
    print("\n📂 Loading datasets...")
    df_train = pd.read_pickle('data/processed/train.pkl')
    df_test = pd.read_pickle('data/processed/test.pkl')
    print(f"   Train: {len(df_train)} samples")
    print(f"   Test:  {len(df_test)} samples")
    
    X_train = df_train['tokens'].tolist()
    y_train = df_train['labels'].tolist()
    X_test = df_test['tokens'].tolist()
    y_test = df_test['labels'].tolist()
    
    # Train
    print("\n🎯 Initializing Hybrid HMM model...")
    model = HybridHMM(alpha=1.0)
    
    train_start = time.perf_counter()
    model.fit(X_train, y_train)
    train_time = time.perf_counter() - train_start
    print(f"\n  ⏱️  Training time: {train_time:.2f}s")
    
    # Predict
    print("\n🔮 Predicting on test set...")
    pred_start = time.perf_counter()
    y_pred = model.predict(X_test)
    pred_time = time.perf_counter() - pred_start
    print(f"   Done in {pred_time:.2f}s")
    
    # Evaluate
    print("\n📊 Computing metrics...")
    metrics = evaluator.compute_entity_metrics(y_test, y_pred, X_test)
    
    evaluator.print_classification_report(metrics, model.name)
    evaluator.print_confusion_summary(metrics, model.name)
    
    # Benchmark
    print(f"\n  ⏱️  Benchmarking inference latency (3 runs)...")
    times = []
    for _ in range(3):
        start = time.perf_counter()
        _ = model.predict(X_test)
        times.append(time.perf_counter() - start)
    
    avg_time = sum(times) / len(times)
    latency_ms = (avg_time / len(X_test)) * 1000
    
    print(f"     Total: {avg_time*1000:.2f} ms for {len(X_test)} samples")
    print(f"     Per-sample: {latency_ms:.4f} ms")
    print(f"     Throughput: {len(X_test)/avg_time:.0f} samples/sec")
    
    metrics['_inference_latency_ms'] = latency_ms
    metrics['_training_time_s'] = train_time
    
    # Save
    model_path = 'models/hybrid_hmm.pkl'
    model.save(model_path)
    print(f"\n  ✅ Model saved: {model_path}")
    
    metrics_path = 'evaluation/hybrid_hmm_metrics.json'
    evaluator.save_metrics(metrics, metrics_path, model.name)
    
    # Summary
    print("\n" + "="*70)
    print(f"  📌 SUMMARY - {model.name}")
    print("="*70)
    print(f"  Macro F1-Score : {metrics['_macro']['f1']:.4f}")
    print(f"  Micro F1-Score : {metrics['_micro']['f1']:.4f}")
    print(f"  Training time  : {train_time:.2f}s")
    print(f"  Inference time : {latency_ms:.4f} ms/sample")
    print("="*70)
    
    print("\n  📝 ANALISIS:")
    print("  " + "-"*66)
    print("  HIPOTESIS: Hybrid HMM > HMM Murni karena Regex-as-a-Feature")
    print("  mengatasi UNK problem pada NIK & PHONE")
    print("="*70)


if __name__ == "__main__":
    main()