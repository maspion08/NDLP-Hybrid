"""
Model 5: Hybrid CRF (CRF + Regex-as-a-Feature)
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Sesuai Bab II.1.11 Proposal:
"hasil pencocokan dari regular expression... dikonversi menjadi fitur 
masukan tambahan (auxiliary feature) bagi model NER"

Strategi:
- CRF dengan SEMUA fitur dari CRF Murni (29+ fitur)
- PLUS fitur regex biner: regex.is_nik dan regex.is_phone
- Diharapkan hasil terbaik karena kombinasi:
  - Word shape, prefix/suffix, context (CRF strength)
  - Pattern matching deterministic (Regex strength)
"""
import os
import sys
import time
import pickle
import pandas as pd
from sklearn_crfsuite import CRF

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
features_module = import_module('07_features')
evaluator = import_module('08_evaluator')


def main():
    print("="*70)
    print("  🤖 MODEL 5: HYBRID CRF (CRF + Regex-as-a-Feature)")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*70)
    
    print("\n📚 STRATEGI HYBRID CRF:")
    print("   - Semua fitur CRF Murni (29+ fitur)")
    print("   - PLUS regex.is_nik dan regex.is_phone (binary features)")
    print("   - Best of both worlds:")
    print("     * Pattern matching (Regex strength)")
    print("     * Contextual features (CRF strength)")
    
    # Load data
    print("\n📂 Loading datasets...")
    df_train = pd.read_pickle('data/processed/train.pkl')
    df_test = pd.read_pickle('data/processed/test.pkl')
    print(f"   Train: {len(df_train)} samples")
    print(f"   Test:  {len(df_test)} samples")
    
    # Feature Engineering WITH regex features
    print("\n🔧 Extracting features (WITH Regex-as-a-Feature)...")
    print("   Train set:")
    X_train, y_train = features_module.dataset_to_features(
        df_train, use_regex_features=True, verbose=True
    )
    
    print("   Test set:")
    X_test, y_test = features_module.dataset_to_features(
        df_test, use_regex_features=True, verbose=True
    )
    
    tokens_test = df_test['tokens'].tolist()
    
    # Initialize CRF (same hyperparameters as CRF Murni for fair comparison)
    print("\n🎯 Initializing Hybrid CRF model...")
    print("   Algorithm: L-BFGS")
    print("   Regularization: L1 (c1=0.1) + L2 (c2=0.1)")
    print("   Max iterations: 100")
    
    crf = CRF(
        algorithm='lbfgs',
        c1=0.1,
        c2=0.1,
        max_iterations=100,
        all_possible_transitions=True,
        verbose=False
    )
    
    # Train
    print("\n🏋️  Training Hybrid CRF...")
    train_start = time.perf_counter()
    crf.fit(X_train, y_train)
    train_time = time.perf_counter() - train_start
    print(f"   ⏱️  Training time: {train_time:.2f}s")
    
    # Predict
    print("\n🔮 Predicting on test set...")
    pred_start = time.perf_counter()
    y_pred = crf.predict(X_test)
    pred_time = time.perf_counter() - pred_start
    print(f"   Done in {pred_time:.2f}s")
    
    # Evaluate
    print("\n📊 Computing metrics...")
    metrics = evaluator.compute_entity_metrics(y_test, y_pred, tokens_test)
    
    model_name = "Hybrid_CRF"
    evaluator.print_classification_report(metrics, model_name)
    evaluator.print_confusion_summary(metrics, model_name)
    
    # Benchmark
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
    
    # Save
    model_path = 'models/hybrid_crf.pkl'
    os.makedirs('models', exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump(crf, f)
    print(f"\n  ✅ Model saved: {model_path}")
    
    metrics_path = 'evaluation/hybrid_crf_metrics.json'
    evaluator.save_metrics(metrics, metrics_path, model_name)
    
    # Show top regex feature weights
    print("\n  🎯 TOP STATE-FEATURE TRANSITIONS (Regex impact):")
    print("  " + "-"*66)
    if hasattr(crf, 'state_features_'):
        # Filter only regex features
        regex_features = [
            ((feat, state), weight) 
            for (feat, state), weight in crf.state_features_.items()
            if 'regex' in feat
        ]
        regex_features.sort(key=lambda x: -abs(x[1]))
        for (feat, state), weight in regex_features[:10]:
            print(f"     {feat:<25} -> {state:<15}: {weight:+.4f}")
    
    # Summary
    print("\n" + "="*70)
    print(f"  📌 SUMMARY - {model_name}")
    print("="*70)
    print(f"  Macro F1-Score : {metrics['_macro']['f1']:.4f}")
    print(f"  Micro F1-Score : {metrics['_micro']['f1']:.4f}")
    print(f"  Training time  : {train_time:.2f}s")
    print(f"  Inference time : {latency_ms:.4f} ms/sample")
    print("="*70)


if __name__ == "__main__":
    main()