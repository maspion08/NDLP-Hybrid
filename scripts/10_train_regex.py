"""
Model 1: Regex Murni (Baseline)
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Sesuai Bab III.3.c.3 Proposal:
- Baseline menggunakan Regular Expression murni
- Mendeteksi NIK dan PHONE pattern
- TIDAK bisa mendeteksi NAMA, JABATAN, LOKASI (karena tidak ada pola)
- Berfungsi sebagai upper-bound untuk PII terstruktur
"""
import os
import sys
import re
import json
import pickle
import time
import pandas as pd
from tqdm import tqdm

# Add scripts to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from importlib import import_module
evaluator = import_module('08_evaluator')


class RegexModel:
    """
    Pure Regex-based PII Detector.
    Hanya mendeteksi entity yang punya pola tetap (NIK, PHONE).
    """
    
    def __init__(self):
        self.patterns = {
            'NIK': re.compile(r'^\d{16}$'),
            'PHONE': re.compile(r'^(?:\+62|0)\d{8,12}$'),
        }
        self.name = "Regex_Murni"
    
    def predict_token(self, token):
        """Predict label untuk single token"""
        for entity_type, pattern in self.patterns.items():
            if pattern.match(token):
                return f'B-{entity_type}'
        return 'O'
    
    def predict_sequence(self, tokens):
        """Predict labels untuk sequence of tokens"""
        return [self.predict_token(token) for token in tokens]
    
    def predict(self, X_tokens):
        """Predict untuk seluruh dataset"""
        return [self.predict_sequence(tokens) for tokens in X_tokens]
    
    def save(self, path):
        """Save model (regex tidak butuh training, tapi save untuk konsistensi)"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'patterns': {k: v.pattern for k, v in self.patterns.items()},
                'name': self.name
            }, f)
    
    @classmethod
    def load(cls, path):
        """Load model dari file"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        model = cls()
        model.patterns = {k: re.compile(v) for k, v in data['patterns'].items()}
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
    print("  🤖 MODEL 1: REGEX MURNI (Baseline)")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*70)
    
    # === Load data ===
    print("\n📂 Loading test set...")
    df_test = pd.read_pickle('data/processed/test.pkl')
    print(f"   Test samples: {len(df_test)}")
    
    # Extract tokens & true labels
    X_tokens = df_test['tokens'].tolist()
    y_true = df_test['labels'].tolist()
    
    # === Initialize model ===
    print("\n🔧 Initializing Regex model...")
    model = RegexModel()
    print(f"   Patterns: {list(model.patterns.keys())}")
    
    # === Predict ===
    print("\n🔮 Predicting on test set...")
    start = time.perf_counter()
    y_pred = model.predict(X_tokens)
    pred_time = time.perf_counter() - start
    print(f"   Done in {pred_time:.2f}s")
    
    # === Evaluate ===
    print("\n📊 Computing metrics...")
    metrics = evaluator.compute_entity_metrics(y_true, y_pred, X_tokens)
    
    # === Print Reports ===
    evaluator.print_classification_report(metrics, model.name)
    evaluator.print_confusion_summary(metrics, model.name)
    
    # === Inference Benchmark ===
    latency = benchmark_inference(model, X_tokens, n_runs=3)
    metrics['_inference_latency_ms'] = latency
    
    # === Save Model ===
    model_path = 'models/regex_baseline.pkl'
    model.save(model_path)
    print(f"\n  ✅ Model saved: {model_path}")
    
    # === Save Metrics ===
    metrics_path = 'evaluation/regex_metrics.json'
    evaluator.save_metrics(metrics, metrics_path, model.name)
    
    # === Final Summary ===
    print("\n" + "="*70)
    print(f"  📌 SUMMARY - {model.name}")
    print("="*70)
    print(f"  Macro F1-Score : {metrics['_macro']['f1']:.4f}")
    print(f"  Micro F1-Score : {metrics['_micro']['f1']:.4f}")
    print(f"  Inference time : {latency:.4f} ms/sample")
    print(f"  Model file     : {model_path}")
    print(f"  Metrics file   : {metrics_path}")
    print("="*70)
    
    print("\n  📝 ANALISIS:")
    print("  " + "-"*66)
    print("  ✓ Regex baik untuk NIK & PHONE (pattern fixed)")
    print("  ✗ Regex GAGAL untuk NAMA, JABATAN, LOKASI (no pattern)")
    print("  → Inilah yang mau dibuktikan: model statistik (HMM/CRF)")
    print("    mampu menangani entity tanpa pattern fixed")
    print("="*70)


if __name__ == "__main__":
    main()