"""
Train Hybrid CRF v2 dengan Rich Feature Engineering
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Features yang digunakan:
- 29 existing CRF features
- 4 context-aware regex features (NEW)
- 3 structural validation features (NEW)
- 5 gazetteer features (NEW)
- 2 negative context features (KILLER FEATURE)
- 2 n-gram pattern features (NEW)

TOTAL: ~45 features per token
"""
import os
import sys
import time
import pickle
import pandas as pd
from sklearn_crfsuite import CRF

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
features_v2 = import_module('07_features_v2')
evaluator = import_module('08_evaluator')


def main():
    print("="*70)
    print("  🤖 MODEL: HYBRID CRF v2 (Rich Feature Engineering)")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*70)
    
    print("\n📚 STRATEGI v2:")
    print("   A. Existing CRF features (29)")
    print("   B. Context-aware regex features (4) - has_nik_label, etc")
    print("   C. Structural validation (3) - nik_province_valid, etc")
    print("   D. Gazetteer lookup (5) - in_jabatan, in_lokasi, etc")
    print("   E. NEGATIVE CONTEXT (2) - anti-FP killer feature")
    print("   F. N-gram patterns (2) - bigram_jabatan_phrase")
    print("   TOTAL: ~45 features per token")
    
    # Load data
    print("\n📂 Loading datasets...")
    df_train = pd.read_pickle('data/processed/train.pkl')
    df_test = pd.read_pickle('data/processed/test.pkl')
    print(f"   Train: {len(df_train)} samples")
    print(f"   Test:  {len(df_test)} samples")
    
    # Feature Engineering with v2
    print("\n🔧 Extracting features (v2 - Rich Engineering)...")
    print("   Train set:")
    X_train, y_train = features_v2.dataset_to_features_v2(
        df_train, use_regex_features=True, use_gazetteer=True, verbose=True
    )
    
    print("   Test set:")
    X_test, y_test = features_v2.dataset_to_features_v2(
        df_test, use_regex_features=True, use_gazetteer=True, verbose=True
    )
    
    tokens_test = df_test['tokens'].tolist()
    
    # Initialize CRF
    print("\n🎯 Initializing Hybrid CRF v2 model...")
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
    print("\n🏋️ Training Hybrid CRF v2...")
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
    
    model_name = "Hybrid_CRF_v2"
    evaluator.print_classification_report(metrics, model_name)
    evaluator.print_confusion_summary(metrics, model_name)
    
    # Benchmark inference latency
    print(f"\n  ⏱️ Benchmarking inference latency (3 runs)...")
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
    
    # Save model
    model_path = 'models/hybrid_crf_v2.pkl'
    os.makedirs('models', exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump(crf, f)
    print(f"\n  ✅ Model saved: {model_path}")
    
    metrics_path = 'evaluation/hybrid_crf_v2_metrics.json'
    evaluator.save_metrics(metrics, metrics_path, model_name)
    
    # Show top NEW feature weights
    print("\n  🎯 TOP NEW FEATURE WEIGHTS:")
    print("  " + "-"*66)
    
    if hasattr(crf, 'state_features_'):
        # Filter new features only
        new_feature_prefixes = ['gazetteer.', 'ngram.', 'regex.has_', 
                                'regex.nik_', 'regex.phone_', 'regex.in_']
        
        new_features = [
            ((feat, state), weight) 
            for (feat, state), weight in crf.state_features_.items()
            if any(feat.startswith(p) for p in new_feature_prefixes)
        ]
        new_features.sort(key=lambda x: -abs(x[1]))
        
        for (feat, state), weight in new_features[:15]:
            print(f"     {feat:<40} -> {state:<12}: {weight:+.4f}")
    
    # Summary
    print("\n" + "="*70)
    print(f"  📌 SUMMARY - {model_name}")
    print("="*70)
    print(f"  Macro F1-Score : {metrics['_macro']['f1']:.4f}")
    print(f"  Micro F1-Score : {metrics['_micro']['f1']:.4f}")
    print(f"  Training time  : {train_time:.2f}s")
    print(f"  Inference time : {latency_ms:.4f} ms/sample")
    print("="*70)
    
    print("\n  📝 NEXT STEP: Evaluate v2 di Holdout + Hard Adversarial")
    print("  Run: python scripts/27_evaluate_crf_v2.py")


if __name__ == "__main__":
    main()