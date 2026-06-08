"""
Evaluate Hybrid CRF v2 di Holdout + Hard Adversarial
Compare dengan CRF Murni dan Hybrid CRF v1
"""
import os
import sys
import json
import time
import pickle
import pandas as pd
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
features_v2 = import_module('07_features_v2')
features_v1 = import_module('07_features')
evaluator = import_module('08_evaluator')


def main():
    print("="*70)
    print("  🎯 EVALUATE HYBRID CRF v2 vs CRF Murni vs Hybrid CRF v1")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*70)
    
    # ============================================================
    # PART 1: Holdout Evaluation
    # ============================================================
    print("\n" + "="*70)
    print("  PART 1: HOLDOUT NATURALISTIC EVALUATION (1000 samples)")
    print("="*70)
    
    df_holdout = pd.read_pickle('data/test_holdout/naturalistic_bio.pkl')
    print(f"\n📂 Loaded: {len(df_holdout)} naturalistic samples")
    
    tokens_holdout = df_holdout['tokens'].tolist()
    
    # 1.1 CRF Murni
    print("\n🤖 Evaluating CRF Murni on holdout...")
    with open('models/crf_pure.pkl', 'rb') as f:
        crf_pure = pickle.load(f)
    X_pure, y_true = features_v1.dataset_to_features(
        df_holdout, use_regex_features=False, verbose=False
    )
    y_pred_pure = crf_pure.predict(X_pure)
    metrics_pure = evaluator.compute_entity_metrics(y_true, y_pred_pure, tokens_holdout)
    print(f"   CRF Murni F1: {metrics_pure['_macro']['f1']:.4f}")
    
    # 1.2 Hybrid CRF v1
    print("\n🤖 Evaluating Hybrid CRF v1 on holdout...")
    with open('models/hybrid_crf.pkl', 'rb') as f:
        crf_v1 = pickle.load(f)
    X_v1, _ = features_v1.dataset_to_features(
        df_holdout, use_regex_features=True, verbose=False
    )
    y_pred_v1 = crf_v1.predict(X_v1)
    metrics_v1 = evaluator.compute_entity_metrics(y_true, y_pred_v1, tokens_holdout)
    print(f"   Hybrid CRF v1 F1: {metrics_v1['_macro']['f1']:.4f}")
    
    # 1.3 Hybrid CRF v2
    print("\n🤖 Evaluating Hybrid CRF v2 on holdout...")
    with open('models/hybrid_crf_v2.pkl', 'rb') as f:
        crf_v2 = pickle.load(f)
    X_v2, _ = features_v2.dataset_to_features_v2(
        df_holdout, use_regex_features=True, use_gazetteer=True, verbose=False
    )
    y_pred_v2 = crf_v2.predict(X_v2)
    metrics_v2 = evaluator.compute_entity_metrics(y_true, y_pred_v2, tokens_holdout)
    print(f"   Hybrid CRF v2 F1: {metrics_v2['_macro']['f1']:.4f}")
    
    # ============================================================
    # COMPARISON TABLE: HOLDOUT
    # ============================================================
    print("\n" + "="*70)
    print("  📊 HOLDOUT COMPARISON")
    print("="*70)
    
    entities = ['NIK', 'PHONE', 'NAMA', 'JABATAN', 'LOKASI']
    
    print(f"\n  {'Model':<18}", end="")
    for ent in entities:
        print(f" {ent:>10}", end="")
    print(f" {'Macro F1':>10}")
    print("  " + "-"*84)
    
    for name, m in [('CRF Murni', metrics_pure), 
                    ('Hybrid CRF v1', metrics_v1), 
                    ('Hybrid CRF v2', metrics_v2)]:
        print(f"  {name:<18}", end="")
        for ent in entities:
            f1 = m.get(ent, {}).get('f1', 0)
            print(f" {f1:>10.4f}", end="")
        print(f" {m['_macro']['f1']:>10.4f}")
    
    # Improvement analysis
    print("\n  📈 IMPROVEMENT ANALYSIS:")
    imp_vs_pure = metrics_v2['_macro']['f1'] - metrics_pure['_macro']['f1']
    imp_vs_v1 = metrics_v2['_macro']['f1'] - metrics_v1['_macro']['f1']
    
    print(f"     v2 vs CRF Murni  : {imp_vs_pure:+.4f} ({imp_vs_pure*100:+.2f}%)")
    print(f"     v2 vs Hybrid v1  : {imp_vs_v1:+.4f} ({imp_vs_v1*100:+.2f}%)")
    
    if imp_vs_pure > 0:
        print(f"\n  🏆 Hybrid CRF v2 MENANG di Holdout!")
    else:
        print(f"\n  ⚠️ Hybrid CRF v2 belum mengalahkan CRF Murni di Holdout")
    
    # ============================================================
    # PART 2: Hard Adversarial Evaluation
    # ============================================================
    print("\n" + "="*70)
    print("  PART 2: HARD ADVERSARIAL EVALUATION (500 samples)")
    print("="*70)
    
    if not os.path.exists('data/raw/hard_adversarial_bio.pkl'):
        print("  ❌ Hard adversarial BIO not found.")
        print("     Run scripts/23_test_hard_adversarial.py first")
        return
    
    df_hard = pd.read_pickle('data/raw/hard_adversarial_bio.pkl')
    print(f"\n📂 Loaded: {len(df_hard)} hard adversarial samples")
    
    # Compute FP rate per category for all 3 models
    categories = df_hard['category'].unique()
    
    def evaluate_on_hard(model, model_name, use_v2_features):
        """Evaluate model pada hard adversarial per kategori"""
        cat_results = {}
        
        for cat in categories:
            cat_df = df_hard[df_hard['category'] == cat]
            
            if use_v2_features:
                X = []
                for tokens in cat_df['tokens']:
                    feats = features_v2.sentence_to_features_v2(
                        tokens, use_regex_features=True, use_gazetteer=True
                    )
                    X.append(feats)
            else:
                X = []
                for tokens in cat_df['tokens']:
                    feats = features_v1.sentence_to_features(
                        tokens, use_regex_features='regex' in model_name.lower()
                    )
                    X.append(feats)
            
            y_pred = model.predict(X)
            
            fp_count = 0
            tp_count = 0
            
            for _, row in cat_df.iterrows():
                idx = list(cat_df.index).index(row.name)
                true_labels = row['labels']
                pred_labels = y_pred[idx]
                
                if all(l == 'O' for l in true_labels):
                    if any(p != 'O' for p in pred_labels):
                        fp_count += 1
                else:
                    has_correct = False
                    for t, true_l, pred_l in zip(row['tokens'], true_labels, pred_labels):
                        if true_l.startswith('B-') and true_l == pred_l:
                            has_correct = True
                            break
                    if has_correct:
                        tp_count += 1
            
            cat_results[cat] = {
                'fp': fp_count,
                'tp': tp_count,
                'total': len(cat_df)
            }
        
        return cat_results
    
    print("\n🔮 Evaluating all 3 models on hard adversarial...")
    results_pure = evaluate_on_hard(crf_pure, 'CRF Murni', use_v2_features=False)
    results_v1 = evaluate_on_hard(crf_v1, 'Hybrid CRF v1', use_v2_features=False)
    results_v2 = evaluate_on_hard(crf_v2, 'Hybrid CRF v2', use_v2_features=True)
    
    # Comparison Table
    print("\n  📊 HARD ADVERSARIAL COMPARISON")
    print("  " + "-"*100)
    print(f"  {'Model':<18}", end="")
    for cat in categories:
        cat_short = cat[:18]
        print(f" {cat_short:<18}", end="")
    print(f" {'Score':>8}")
    print("  " + "-"*100)
    
    for name, results in [('CRF Murni', results_pure),
                          ('Hybrid CRF v1', results_v1),
                          ('Hybrid CRF v2', results_v2)]:
        print(f"  {name:<18}", end="")
        total_tp = 0
        total_fp = 0
        
        for cat in categories:
            r = results[cat]
            if cat.startswith('context_free') or cat == 'near_pattern':
                fp_rate = r['fp'] / r['total'] * 100
                marker = '❌' if fp_rate > 30 else ('⚠️ ' if fp_rate > 10 else '✅')
                print(f" {marker}FP:{fp_rate:>4.1f}%       ", end="")
                total_fp += r['fp']
            else:
                tp_rate = r['tp'] / r['total'] * 100
                marker = '✅' if tp_rate > 80 else ('⚠️ ' if tp_rate > 50 else '❌')
                print(f" {marker}TP:{tp_rate:>4.1f}%       ", end="")
                total_tp += r['tp']
        
        score = total_tp - total_fp
        print(f" {score:>+8d}")
    
    # ============================================================
    # FINAL CONCLUSION
    # ============================================================
    print("\n" + "="*70)
    print("  🏆 FINAL VERDICT: Hybrid CRF v2 Performance")
    print("="*70)
    
    score_pure = sum([r['tp'] for c, r in results_pure.items() if not (c.startswith('context_free') or c == 'near_pattern')]) - \
                 sum([r['fp'] for c, r in results_pure.items() if c.startswith('context_free') or c == 'near_pattern'])
    
    score_v1 = sum([r['tp'] for c, r in results_v1.items() if not (c.startswith('context_free') or c == 'near_pattern')]) - \
               sum([r['fp'] for c, r in results_v1.items() if c.startswith('context_free') or c == 'near_pattern'])
    
    score_v2 = sum([r['tp'] for c, r in results_v2.items() if not (c.startswith('context_free') or c == 'near_pattern')]) - \
               sum([r['fp'] for c, r in results_v2.items() if c.startswith('context_free') or c == 'near_pattern'])
    
    print(f"\n  HOLDOUT F1:")
    print(f"     CRF Murni      : {metrics_pure['_macro']['f1']:.4f}")
    print(f"     Hybrid CRF v1  : {metrics_v1['_macro']['f1']:.4f}")
    print(f"     Hybrid CRF v2  : {metrics_v2['_macro']['f1']:.4f}  {'⭐ BEST' if metrics_v2['_macro']['f1'] >= max(metrics_pure['_macro']['f1'], metrics_v1['_macro']['f1']) else ''}")
    
    print(f"\n  HARD ADVERSARIAL SCORE:")
    print(f"     CRF Murni      : {score_pure:+d}")
    print(f"     Hybrid CRF v1  : {score_v1:+d}")
    print(f"     Hybrid CRF v2  : {score_v2:+d}  {'⭐ BEST' if score_v2 >= max(score_pure, score_v1) else ''}")
    
    print()
    if metrics_v2['_macro']['f1'] > metrics_pure['_macro']['f1'] and score_v2 > score_pure:
        print("  🎉 SUCCESS: Hybrid CRF v2 MENGALAHKAN CRF Murni di BOTH metrics!")
        print("     ✅ Hipotesis 'Hybrid > Murni' TERBUKTI dengan rich features!")
    elif metrics_v2['_macro']['f1'] > metrics_pure['_macro']['f1']:
        print("  ✅ Hybrid CRF v2 menang di Holdout (out-of-distribution)")
    elif score_v2 > score_pure:
        print("  ✅ Hybrid CRF v2 menang di Hard Adversarial (robustness)")
    else:
        print("  ⚠️ Hybrid CRF v2 belum bisa mengalahkan CRF Murni")
        print("     → Perlu investigasi lebih lanjut")
    
    print("="*70)
    
    # Save results
    results_path = 'evaluation/crf_v2_comparison.json'
    with open(results_path, 'w') as f:
        json.dump({
            'holdout': {
                'CRF_Murni_F1': metrics_pure['_macro']['f1'],
                'Hybrid_CRF_v1_F1': metrics_v1['_macro']['f1'],
                'Hybrid_CRF_v2_F1': metrics_v2['_macro']['f1'],
            },
            'hard_adversarial': {
                'CRF_Murni_Score': score_pure,
                'Hybrid_CRF_v1_Score': score_v1,
                'Hybrid_CRF_v2_Score': score_v2,
            }
        }, f, indent=2)
    
    print(f"\n  ✅ Results saved: {results_path}")


if __name__ == "__main__":
    main()