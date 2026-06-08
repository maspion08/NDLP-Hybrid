"""
Holdout Evaluation: Test All 5 Models on Naturalistic Set
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Sesuai Bab III.3.c.1 Proposal:
"...digunakan sebagai held-out test set tambahan untuk mengukur 
kesenjangan performa (performance gap) antara kondisi sintetis 
dan naturalistik."

OBJECTIVE:
==========
1. Evaluate all 5 models on 1.000 naturalistic samples
2. Compare Test F1 vs Holdout F1 → performance gap
3. Identify which model has best generalization
4. Generate final comparison table for Bab IV laporan

KEY INSIGHT TO LOOK FOR:
========================
- CRF Murni F1=1.0 di test → akan turun di holdout?
- Hybrid CRF lebih robust di holdout?
- HMM Murni vs Hybrid HMM gap di holdout?
"""
import os
import sys
import json
import time
import pickle
import pandas as pd
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
features_module = import_module('07_features')
evaluator = import_module('08_evaluator')


def load_holdout():
    """Load holdout naturalistic test set"""
    path = 'data/test_holdout/naturalistic_bio.pkl'
    if not os.path.exists(path):
        print(f"❌ Holdout not found: {path}")
        print("   Run scripts\\18_tag_holdout.py first")
        return None
    return pd.read_pickle(path)


def evaluate_regex(df_holdout):
    """Evaluate Regex Murni on holdout"""
    print("\n" + "="*70)
    print("  🤖 EVALUATING: Regex Murni")
    print("="*70)
    
    if not os.path.exists('models/regex_baseline.pkl'):
        return None
    
    regex_module = import_module('10_train_regex')
    model = regex_module.RegexModel.load('models/regex_baseline.pkl')
    
    X_tokens = df_holdout['tokens'].tolist()
    y_true = df_holdout['labels'].tolist()
    
    start = time.perf_counter()
    y_pred = model.predict(X_tokens)
    elapsed = time.perf_counter() - start
    
    metrics = evaluator.compute_entity_metrics(y_true, y_pred, X_tokens)
    metrics['_inference_time_s'] = elapsed
    
    return metrics


def evaluate_hmm(df_holdout):
    """Evaluate HMM Murni on holdout"""
    print("\n" + "="*70)
    print("  🤖 EVALUATING: HMM Murni")
    print("="*70)
    
    if not os.path.exists('models/hmm_pure.pkl'):
        return None
    
    hmm_module = import_module('11_train_hmm')
    model = hmm_module.CategoricalHMM.load('models/hmm_pure.pkl')
    
    X_tokens = df_holdout['tokens'].tolist()
    y_true = df_holdout['labels'].tolist()
    
    start = time.perf_counter()
    y_pred = model.predict(X_tokens)
    elapsed = time.perf_counter() - start
    
    metrics = evaluator.compute_entity_metrics(y_true, y_pred, X_tokens)
    metrics['_inference_time_s'] = elapsed
    
    return metrics


def evaluate_crf(df_holdout):
    """Evaluate CRF Murni on holdout"""
    print("\n" + "="*70)
    print("  🤖 EVALUATING: CRF Murni")
    print("="*70)
    
    if not os.path.exists('models/crf_pure.pkl'):
        return None
    
    with open('models/crf_pure.pkl', 'rb') as f:
        model = pickle.load(f)
    
    X_features, y_true = features_module.dataset_to_features(
        df_holdout, use_regex_features=False, verbose=False
    )
    tokens = df_holdout['tokens'].tolist()
    
    start = time.perf_counter()
    y_pred = model.predict(X_features)
    elapsed = time.perf_counter() - start
    
    metrics = evaluator.compute_entity_metrics(y_true, y_pred, tokens)
    metrics['_inference_time_s'] = elapsed
    
    return metrics


def evaluate_hybrid_hmm(df_holdout):
    """Evaluate Hybrid HMM on holdout"""
    print("\n" + "="*70)
    print("  🤖 EVALUATING: Hybrid HMM")
    print("="*70)
    
    if not os.path.exists('models/hybrid_hmm.pkl'):
        return None
    
    hmm_module = import_module('13_train_hybrid_hmm')
    model = hmm_module.HybridHMM.load('models/hybrid_hmm.pkl')
    
    X_tokens = df_holdout['tokens'].tolist()
    y_true = df_holdout['labels'].tolist()
    
    start = time.perf_counter()
    y_pred = model.predict(X_tokens)
    elapsed = time.perf_counter() - start
    
    metrics = evaluator.compute_entity_metrics(y_true, y_pred, X_tokens)
    metrics['_inference_time_s'] = elapsed
    
    return metrics


def evaluate_hybrid_crf(df_holdout):
    """Evaluate Hybrid CRF on holdout"""
    print("\n" + "="*70)
    print("  🤖 EVALUATING: Hybrid CRF")
    print("="*70)
    
    if not os.path.exists('models/hybrid_crf.pkl'):
        return None
    
    with open('models/hybrid_crf.pkl', 'rb') as f:
        model = pickle.load(f)
    
    X_features, y_true = features_module.dataset_to_features(
        df_holdout, use_regex_features=True, verbose=False
    )
    tokens = df_holdout['tokens'].tolist()
    
    start = time.perf_counter()
    y_pred = model.predict(X_features)
    elapsed = time.perf_counter() - start
    
    metrics = evaluator.compute_entity_metrics(y_true, y_pred, tokens)
    metrics['_inference_time_s'] = elapsed
    
    return metrics


def evaluate_per_format(df_holdout, model_name, predict_fn, model):
    """Evaluate model per holdout format (email, db, json, dll)"""
    print(f"\n  📊 Per-format evaluation - {model_name}")
    print("  " + "-"*60)
    
    format_results = {}
    
    for fmt in df_holdout['format'].unique():
        fmt_df = df_holdout[df_holdout['format'] == fmt]
        
        if model_name in ['Regex_Murni', 'HMM_Murni', 'Hybrid_HMM']:
            X = fmt_df['tokens'].tolist()
            y_true = fmt_df['labels'].tolist()
            y_pred = predict_fn(X)
            tokens = X
        elif model_name == 'CRF_Murni':
            X, y_true = features_module.dataset_to_features(
                fmt_df, use_regex_features=False, verbose=False
            )
            y_pred = predict_fn(X)
            tokens = fmt_df['tokens'].tolist()
        elif model_name == 'Hybrid_CRF':
            X, y_true = features_module.dataset_to_features(
                fmt_df, use_regex_features=True, verbose=False
            )
            y_pred = predict_fn(X)
            tokens = fmt_df['tokens'].tolist()
        
        metrics = evaluator.compute_entity_metrics(y_true, y_pred, tokens)
        macro_f1 = metrics['_macro']['f1']
        format_results[fmt] = macro_f1
        
        print(f"     {fmt:<18}: F1 = {macro_f1:.4f}")
    
    return format_results


def load_test_metrics(model_name):
    """Load previously computed test set metrics"""
    file_map = {
        'Regex_Murni': 'evaluation/regex_metrics.json',
        'HMM_Murni': 'evaluation/hmm_metrics.json',
        'CRF_Murni': 'evaluation/crf_metrics.json',
        'Hybrid_HMM': 'evaluation/hybrid_hmm_metrics.json',
        'Hybrid_CRF': 'evaluation/hybrid_crf_metrics.json',
    }
    
    if model_name not in file_map or not os.path.exists(file_map[model_name]):
        return None
    
    with open(file_map[model_name], 'r') as f:
        data = json.load(f)
    return data['metrics']


def main():
    print("="*70)
    print("  🎯 HOLDOUT EVALUATION - All 5 Models")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*70)
    
    print("\n📚 OBJECTIVE:")
    print("   Sesuai proposal Bab III.3.c.1:")
    print("   'mengukur kesenjangan performa (performance gap) antara")
    print("    kondisi sintetis dan naturalistik'")
    
    # Load holdout
    df_holdout = load_holdout()
    if df_holdout is None:
        return
    
    print(f"\n📂 Holdout dataset loaded: {len(df_holdout)} samples")
    print(f"   Formats: {sorted(df_holdout['format'].unique())}")
    
    # Evaluate all models
    results = {}
    
    print("\n" + "="*70)
    print("  🔮 RUNNING EVALUATIONS...")
    print("="*70)
    
    # Each model
    eval_functions = [
        ('Regex_Murni', evaluate_regex),
        ('HMM_Murni', evaluate_hmm),
        ('CRF_Murni', evaluate_crf),
        ('Hybrid_HMM', evaluate_hybrid_hmm),
        ('Hybrid_CRF', evaluate_hybrid_crf),
    ]
    
    for model_name, eval_fn in eval_functions:
        metrics = eval_fn(df_holdout)
        if metrics:
            results[model_name] = metrics
            evaluator.print_classification_report(metrics, model_name)
    
    # === FINAL COMPARISON TABLE ===
    print("\n\n" + "="*80)
    print("  🏆 FINAL COMPARISON: TEST SET vs HOLDOUT")
    print("="*80)
    
    # Header
    print(f"\n  {'Model':<15} {'Test F1':>10} {'Holdout F1':>12} {'Gap':>10} {'Status':<15}")
    print("  " + "-"*70)
    
    comparison = []
    for model_name in ['Regex_Murni', 'HMM_Murni', 'CRF_Murni', 'Hybrid_HMM', 'Hybrid_CRF']:
        if model_name not in results:
            continue
        
        test_metrics = load_test_metrics(model_name)
        holdout_metrics = results[model_name]
        
        test_f1 = test_metrics['_macro']['f1'] if test_metrics else 0
        holdout_f1 = holdout_metrics['_macro']['f1']
        gap = test_f1 - holdout_f1
        
        # Status indicator
        if gap < 0.05:
            status = "✅ Robust"
        elif gap < 0.15:
            status = "⚠️ Mild gap"
        else:
            status = "❌ Large gap"
        
        comparison.append({
            'model': model_name,
            'test_f1': test_f1,
            'holdout_f1': holdout_f1,
            'gap': gap,
            'status': status
        })
        
        print(f"  {model_name:<15} {test_f1:>10.4f} {holdout_f1:>12.4f} {gap:>+10.4f}  {status}")
    
    print("  " + "-"*70)
    
    # === PER-ENTITY ANALYSIS ===
    print("\n\n" + "="*80)
    print("  📊 PER-ENTITY F1-SCORE on HOLDOUT")
    print("="*80)
    
    entities = ['NIK', 'PHONE', 'NAMA', 'JABATAN', 'LOKASI']
    
    print(f"\n  {'Model':<15}", end="")
    for ent in entities:
        print(f" {ent:>10}", end="")
    print(f" {'Macro':>10}")
    print("  " + "-"*78)
    
    for model_name in ['Regex_Murni', 'HMM_Murni', 'CRF_Murni', 'Hybrid_HMM', 'Hybrid_CRF']:
        if model_name not in results:
            continue
        
        m = results[model_name]
        print(f"  {model_name:<15}", end="")
        for ent in entities:
            f1 = m.get(ent, {}).get('f1', 0) if ent in m else 0
            print(f" {f1:>10.4f}", end="")
        print(f" {m['_macro']['f1']:>10.4f}")
    
    # === BEST MODEL ===
    print("\n" + "="*80)
    print("  🏆 BEST MODEL ON HOLDOUT")
    print("="*80)
    
    if comparison:
        best = max(comparison, key=lambda x: x['holdout_f1'])
        print(f"\n  Winner: {best['model']}")
        print(f"  Holdout F1: {best['holdout_f1']:.4f}")
        print(f"  Test F1: {best['test_f1']:.4f}")
        print(f"  Gap: {best['gap']:+.4f}")
        
        # Robustness ranking
        sorted_comp = sorted(comparison, key=lambda x: -x['holdout_f1'])
        print(f"\n  Robustness Ranking (by Holdout F1):")
        for i, c in enumerate(sorted_comp, 1):
            print(f"     {i}. {c['model']:<15} F1={c['holdout_f1']:.4f} Gap={c['gap']:+.4f}")
    
    # === Save results ===
    os.makedirs('evaluation', exist_ok=True)
    
    final_results = {
        'comparison': comparison,
        'per_model_holdout': {k: v for k, v in results.items()},
        'analysis': {
            'best_model_holdout': best['model'] if comparison else None,
            'best_f1_holdout': best['holdout_f1'] if comparison else None,
        }
    }
    
    output_path = 'evaluation/holdout_results.json'
    with open(output_path, 'w') as f:
        # Convert non-serializable
        serializable = json.loads(json.dumps(final_results, default=str))
        json.dump(serializable, f, indent=2)
    
    print(f"\n  ✅ Results saved: {output_path}")
    print("="*80)


if __name__ == "__main__":
    main()