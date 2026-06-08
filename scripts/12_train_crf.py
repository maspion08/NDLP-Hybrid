"""
Model 3: CRF Murni (Conditional Random Fields)
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Sesuai Bab II.1.10 Proposal:
- Linear-Chain CRF (sklearn-crfsuite)
- Algoritma L-BFGS dengan regularisasi L1+L2
- Fitur: word identity, prefix/suffix, word shape, posisi
- TANPA Regex-as-a-Feature (untuk fair comparison dengan Hybrid CRF)

Referensi formula:
    P(y|x) = (1/Z(x)) × exp(Σ Σ λ_j × f_j(y_{t-1}, y_t, x, t))
"""
import os
import sys
import time
import pickle
import pandas as pd
from tqdm import tqdm
from sklearn_crfsuite import CRF

# Add scripts to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
features_module = import_module('07_features')
evaluator = import_module('08_evaluator')


def main():
    print("="*70)
    print("  🤖 MODEL 3: CRF MURNI (Conditional Random Fields)")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*70)
    
    # === Load data ===
    print("\n📂 Loading datasets...")
    df_train = pd.read_pickle('data/processed/train.pkl')
    df_val = pd.read_pickle('data/processed/val.pkl')
    df_test = pd.read_pickle('data/processed/test.pkl')
    print(f"   Train: {len(df_train)} samples")
    print(f"   Val:   {len(df_val)} samples")
    print(f"   Test:  {len(df_test)} samples")
    
    # === Feature Engineering (NO regex features) ===
    print("\n🔧 Extracting features (NO Regex-as-a-Feature)...")
    print("   Train set:")
    X_train, y_train = features_module.dataset_to_features(
        df_train, use_regex_features=False, verbose=True
    )
    
    print("   Test set:")
    X_test, y_test = features_module.dataset_to_features(
        df_test, use_regex_features=False, verbose=True
    )
    
    # Tokens for evaluation
    tokens_test = df_test['tokens'].tolist()
    
    # === Initialize CRF ===
    print("\n🎯 Initializing CRF model...")
    print("   Algorithm: L-BFGS")
    print("   Regularization: L1 (c1=0.1) + L2 (c2=0.1)")
    print("   Max iterations: 100")
    
    crf = CRF(
        algorithm='lbfgs',
        c1=0.1,                    # L1 regularization
        c2=0.1,                    # L2 regularization
        max_iterations=100,
        all_possible_transitions=True,
        verbose=False
    )
    
    # === Train ===
    print("\n🏋️  Training CRF...")
    train_start = time.perf_counter()
    crf.fit(X_train, y_train)
    train_time = time.perf_counter() - train_start
    print(f"   ⏱️  Training time: {train_time:.2f}s")
    
    # === Predict ===
    print("\n🔮 Predicting on test set...")
    pred_start = time.perf_counter()
    y_pred = crf.predict(X_test)
    pred_time = time.perf_counter() - pred_start
    print(f"   Done in {pred_time:.2f}s")
    
    # === Evaluate ===
    print("\n📊 Computing metrics...")
    metrics = evaluator.compute_entity_metrics(y_test, y_pred, tokens_test)
    
    # === Print Reports ===
    model_name = "CRF_Murni"
    evaluator.print_classification_report(metrics, model_name)
    evaluator.print_confusion_summary(metrics, model_name)
    
    # === Inference Benchmark ===
    print(f"\n  ⏱️  Benchmarking inference latency (3 runs)...")
    times = []
    for _ in range(3):
        start = time.perf_counter()
        _ = crf.predict(X_test)
        times.append(time.perf_counter() - start)
    
    avg_time = sum(times) / len(times)
    latency_ms = (avg_time / len(X_test)) * 1000
    
    print(f"     Total: {avg_time*1000:.2f} ms for {len(X_test)} samples")
    print(f"     Per-sample: {latency_ms:.4f} ms")
    print(f"     Throughput: {len(X_test)/avg_time:.0f} samples/sec")
    
    metrics['_inference_latency_ms'] = latency_ms
    metrics['_training_time_s'] = train_time
    
    # === Save Model ===
    model_path = 'models/crf_pure.pkl'
    os.makedirs('models', exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump(crf, f)
    print(f"\n  ✅ Model saved: {model_path}")
    
    # === Save Metrics ===
    metrics_path = 'evaluation/crf_metrics.json'
    evaluator.save_metrics(metrics, metrics_path, model_name)
    
    # === Summary ===
    print("\n" + "="*70)
    print(f"  📌 SUMMARY - {model_name}")
    print("="*70)
    print(f"  Macro F1-Score : {metrics['_macro']['f1']:.4f}")
    print(f"  Micro F1-Score : {metrics['_micro']['f1']:.4f}")
    print(f"  Training time  : {train_time:.2f}s")
    print(f"  Inference time : {latency_ms:.4f} ms/sample")
    print("="*70)
    
    print("\n  📝 ANALISIS:")
    print("  " + "-"*66)
    if metrics['_macro']['f1'] >= 0.80:
        print(f"  ✅ CRF mencapai target F1 ≥ 0.80!")
        print(f"     CRF lebih baik dari HMM karena pakai fitur kontekstual")
        print(f"     (word shape, prefix/suffix) yang tidak vocabulary-bound.")
    else:
        print(f"  ⚠️  CRF Macro F1 = {metrics['_macro']['f1']:.4f}")
    
    print(f"\n  🆚 KOMPARASI dengan model sebelumnya:")
    print(f"     Regex Murni : 0.4000")
    print(f"     HMM Murni   : 0.6000")
    print(f"     CRF Murni   : {metrics['_macro']['f1']:.4f}")
    
    # Show feature importance (top 10 most useful features per state)
    print("\n  🎯 TOP STATE TRANSITIONS (top 10):")
    print("  " + "-"*66)
    if hasattr(crf, 'transition_features_'):
        sorted_trans = sorted(crf.transition_features_.items(), 
                            key=lambda x: -abs(x[1]))[:10]
        for (from_state, to_state), weight in sorted_trans:
            print(f"     {from_state:<15} -> {to_state:<15}: {weight:.4f}")
    
    print("="*70)


if __name__ == "__main__":
    main()