"""
Model 2: HMM Murni (Hidden Markov Model)
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Sesuai Bab II.1.9 Proposal:
- Categorical HMM (observasi diskret via vocabulary)
- Parameter: start_prob, transition_matrix, emission_matrix
- Estimasi: MLE dengan Laplace Smoothing
- Inference: Viterbi dalam log-space (stabilitas numerik)

Referensi formula:
    P(x,y) = ∏ P(y_t | y_{t-1}) × P(x_t | y_t)
"""
import os
import sys
import time
import pickle
import numpy as np
import pandas as pd
from collections import defaultdict
from tqdm import tqdm

# Add scripts to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
evaluator = import_module('08_evaluator')


class CategoricalHMM:
    """
    Hidden Markov Model dengan observasi diskret (kategorikal).
    
    Implementation:
    - Supervised learning via MLE
    - Laplace smoothing (add-alpha)
    - Viterbi decoding dalam log-space
    """
    
    def __init__(self, alpha=1.0):
        """
        Args:
            alpha: Laplace smoothing parameter (alpha=1 = add-one smoothing)
        """
        self.alpha = alpha
        self.name = "HMM_Murni"
        
        # Akan diisi saat training
        self.states = None         # List of unique labels (e.g. ['O', 'B-NIK', ...])
        self.state_to_idx = None   # Label → integer
        self.vocab = None          # List of unique tokens
        self.token_to_idx = None   # Token → integer
        self.unk_idx = None        # Index untuk unknown tokens
        
        # Parameters
        self.log_start_prob = None     # log P(y_0)
        self.log_trans_prob = None     # log P(y_t | y_{t-1})
        self.log_emission_prob = None  # log P(x_t | y_t)
    
    def fit(self, X_sequences, y_sequences):
        """
        Train HMM via MLE dengan Laplace smoothing.
        
        Args:
            X_sequences: list of token sequences
            y_sequences: list of label sequences
        """
        print("\n  🔧 Training HMM (MLE + Laplace Smoothing)...")
        
        # === Step 1: Build vocabulary & state set ===
        print("     1. Building vocabulary & states...")
        
        # Unique states (labels)
        all_labels = set()
        for seq in y_sequences:
            all_labels.update(seq)
        self.states = sorted(all_labels)
        self.state_to_idx = {s: i for i, s in enumerate(self.states)}
        n_states = len(self.states)
        
        # Unique tokens (lowercase untuk reduce sparsity)
        all_tokens = set()
        for seq in X_sequences:
            all_tokens.update(t.lower() for t in seq)
        
        self.vocab = sorted(all_tokens) + ['<UNK>']
        self.token_to_idx = {t: i for i, t in enumerate(self.vocab)}
        self.unk_idx = self.token_to_idx['<UNK>']
        n_vocab = len(self.vocab)
        
        print(f"        States: {n_states} ({self.states})")
        print(f"        Vocabulary: {n_vocab:,} unique tokens")
        
        # === Step 2: Count statistics ===
        print("     2. Counting frequencies...")
        
        # Count: π(s) = jumlah sequence yang mulai dengan state s
        start_counts = np.zeros(n_states)
        # Count: A(s_i, s_j) = jumlah transisi s_i → s_j
        trans_counts = np.zeros((n_states, n_states))
        # Count: B(s, x) = jumlah emisi token x saat state s
        emission_counts = np.zeros((n_states, n_vocab))
        
        for tokens, labels in tqdm(zip(X_sequences, y_sequences), 
                                    total=len(X_sequences),
                                    desc="        Counting"):
            if not labels:
                continue
            
            # Start probability
            start_counts[self.state_to_idx[labels[0]]] += 1
            
            # Transition & Emission counts
            for i, (token, label) in enumerate(zip(tokens, labels)):
                state_idx = self.state_to_idx[label]
                token_lower = token.lower()
                token_idx = self.token_to_idx.get(token_lower, self.unk_idx)
                
                # Emission count
                emission_counts[state_idx, token_idx] += 1
                
                # Transition count
                if i > 0:
                    prev_state_idx = self.state_to_idx[labels[i-1]]
                    trans_counts[prev_state_idx, state_idx] += 1
        
        # === Step 3: MLE with Laplace Smoothing ===
        print("     3. Computing probabilities (Laplace alpha={:.1f})...".format(self.alpha))
        
        # Start probability: π(s) = (count(s) + α) / (total + α × K)
        start_prob = (start_counts + self.alpha) / \
                     (start_counts.sum() + self.alpha * n_states)
        
        # Transition probability: P(s_j | s_i) = (count(s_i→s_j) + α) / (sum_k count(s_i→s_k) + α × K)
        trans_prob = (trans_counts + self.alpha) / \
                     (trans_counts.sum(axis=1, keepdims=True) + self.alpha * n_states)
        
        # Emission probability: P(x | s) = (count(s,x) + α) / (sum_x count(s,x) + α × V)
        emission_prob = (emission_counts + self.alpha) / \
                        (emission_counts.sum(axis=1, keepdims=True) + self.alpha * n_vocab)
        
        # Convert to log-space (untuk Viterbi numerical stability)
        self.log_start_prob = np.log(start_prob)
        self.log_trans_prob = np.log(trans_prob)
        self.log_emission_prob = np.log(emission_prob)
        
        print(f"     ✅ Training complete")
        print(f"        Start prob shape: {self.log_start_prob.shape}")
        print(f"        Trans prob shape: {self.log_trans_prob.shape}")
        print(f"        Emission prob shape: {self.log_emission_prob.shape}")
    
    def viterbi_decode(self, tokens):
        """
        Viterbi algorithm dalam log-space untuk decode sequence.
        
        Returns:
            list of predicted labels
        """
        n_states = len(self.states)
        T = len(tokens)
        
        if T == 0:
            return []
        
        # Token indices
        token_indices = [self.token_to_idx.get(t.lower(), self.unk_idx) for t in tokens]
        
        # Viterbi matrix
        viterbi = np.full((T, n_states), -np.inf)
        backpointer = np.zeros((T, n_states), dtype=int)
        
        # Initialization: t = 0
        viterbi[0] = self.log_start_prob + self.log_emission_prob[:, token_indices[0]]
        
        # Recursion: t = 1, 2, ..., T-1
        for t in range(1, T):
            for s in range(n_states):
                # log P(y_t = s) = max_{s'} [viterbi[t-1, s'] + log P(s | s') + log P(x_t | s)]
                scores = viterbi[t-1] + self.log_trans_prob[:, s] + self.log_emission_prob[s, token_indices[t]]
                viterbi[t, s] = np.max(scores)
                backpointer[t, s] = np.argmax(scores)
        
        # Backtrace
        best_path = [0] * T
        best_path[T-1] = np.argmax(viterbi[T-1])
        
        for t in range(T-2, -1, -1):
            best_path[t] = backpointer[t+1, best_path[t+1]]
        
        # Convert indices to state labels
        return [self.states[idx] for idx in best_path]
    
    def predict(self, X_tokens):
        """Predict labels untuk seluruh dataset"""
        return [self.viterbi_decode(tokens) for tokens in X_tokens]
    
    def save(self, path):
        """Save model to file"""
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
        """Load model from file"""
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


def benchmark_inference(model, X_tokens, n_runs=3):
    """Benchmark inference latency"""
    print(f"\n  ⏱️  Benchmarking inference latency ({n_runs} runs)...")
    
    times = []
    for run in range(n_runs):
        start = time.perf_counter()
        _ = model.predict(X_tokens)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    per_sample_ms = (avg_time / len(X_tokens)) * 1000
    
    print(f"     Total: {avg_time*1000:.2f} ms for {len(X_tokens)} samples")
    print(f"     Per-sample: {per_sample_ms:.4f} ms")
    print(f"     Throughput: {len(X_tokens)/avg_time:.0f} samples/sec")
    
    return per_sample_ms


def main():
    print("="*70)
    print("  🤖 MODEL 2: HMM MURNI (Hidden Markov Model)")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*70)
    
    # === Load data ===
    print("\n📂 Loading datasets...")
    df_train = pd.read_pickle('data/processed/train.pkl')
    df_test = pd.read_pickle('data/processed/test.pkl')
    print(f"   Train: {len(df_train)} samples")
    print(f"   Test:  {len(df_test)} samples")
    
    # Extract sequences
    X_train = df_train['tokens'].tolist()
    y_train = df_train['labels'].tolist()
    X_test = df_test['tokens'].tolist()
    y_test = df_test['labels'].tolist()
    
    # === Train HMM ===
    print("\n🎯 Initializing HMM model...")
    model = CategoricalHMM(alpha=1.0)  # Laplace alpha = 1 (add-one)
    
    train_start = time.perf_counter()
    model.fit(X_train, y_train)
    train_time = time.perf_counter() - train_start
    print(f"\n  ⏱️  Training time: {train_time:.2f}s")
    
    # === Predict ===
    print("\n🔮 Predicting on test set...")
    pred_start = time.perf_counter()
    y_pred = model.predict(X_test)
    pred_time = time.perf_counter() - pred_start
    print(f"   Done in {pred_time:.2f}s")
    
    # === Evaluate ===
    print("\n📊 Computing metrics...")
    metrics = evaluator.compute_entity_metrics(y_test, y_pred, X_test)
    
    # === Print Reports ===
    evaluator.print_classification_report(metrics, model.name)
    evaluator.print_confusion_summary(metrics, model.name)
    
    # === Inference Benchmark ===
    latency = benchmark_inference(model, X_test, n_runs=3)
    metrics['_inference_latency_ms'] = latency
    metrics['_training_time_s'] = train_time
    
    # === Save ===
    model_path = 'models/hmm_pure.pkl'
    model.save(model_path)
    print(f"\n  ✅ Model saved: {model_path}")
    
    metrics_path = 'evaluation/hmm_metrics.json'
    evaluator.save_metrics(metrics, metrics_path, model.name)
    
    # === Summary ===
    print("\n" + "="*70)
    print(f"  📌 SUMMARY - {model.name}")
    print("="*70)
    print(f"  Macro F1-Score : {metrics['_macro']['f1']:.4f}")
    print(f"  Micro F1-Score : {metrics['_micro']['f1']:.4f}")
    print(f"  Training time  : {train_time:.2f}s")
    print(f"  Inference time : {latency:.4f} ms/sample")
    print("="*70)
    
    print("\n  📝 ANALISIS:")
    print("  " + "-"*66)
    if metrics['_macro']['f1'] >= 0.80:
        print("  ✅ HMM mencapai target F1 ≥ 0.80!")
    else:
        print(f"  ⚠️  HMM Macro F1 = {metrics['_macro']['f1']:.4f} (target ≥ 0.80)")
        print("     Ini wajar karena HMM mengandalkan fitur lokal saja.")
        print("     Diharapkan CRF & Hybrid akan lebih baik.")
    print("="*70)


if __name__ == "__main__":
    main()