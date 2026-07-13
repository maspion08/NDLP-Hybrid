"""
McNemar's Significance Test untuk Model Comparison
Tugas Akhir: Arga Ariyuda Avian (2221101774)
 
TUJUAN:
=======
Membuktikan bahwa perbedaan performa antar model adalah SIGNIFIKAN
SECARA STATISTIK, bukan kebetulan.
 
LANDASAN ILMIAH:
================
1. McNemar (1947) - "Note on the sampling error of the difference
   between correlated proportions or percentages"
 
2. Dietterich (1998) - "Approximate Statistical Tests for Comparing
   Supervised Classification Learning Algorithms"
 
3. Salzberg (1997) - "On Comparing Classifiers: Pitfalls to Avoid
   and a Recommended Approach"
 
PROSEDUR:
=========
Untuk setiap pasangan model, hitung:
- b = sampel yang Model A benar, Model B salah
- c = sampel yang Model A salah, Model B benar
- chi2 = (|b - c| - 1)^2 / (b + c)
- p-value dari distribusi chi-square dengan df=1
 
EVALUASI:
=========
Dilakukan pada Held-Out Naturalistic Set (1000 sampel).
"""
import os
import sys
import json
import pickle
import pandas as pd
from datetime import datetime
from scipy import stats
 
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
 
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
features_v1 = import_module('07_features')
features_v2 = import_module('07_features_v2')
evaluator   = import_module('08_evaluator')
 
 
def mcnemars_test(model_a_correct, model_b_correct):
    if len(model_a_correct) != len(model_b_correct):
        raise ValueError("Length mismatch")
 
    both_correct = a_only = b_only = both_wrong = 0
    for a, b in zip(model_a_correct, model_b_correct):
        if a and b:     both_correct += 1
        elif a and not b: a_only += 1
        elif not a and b: b_only += 1
        else:            both_wrong += 1
 
    b_val = a_only
    c_val = b_only
    n_dis = b_val + c_val
 
    if n_dis == 0:
        return {
            'b': b_val, 'c': c_val,
            'both_correct': both_correct, 'both_wrong': both_wrong,
            'chi_square': 0.0, 'p_value': 1.0,
            'significance': 'No disagreement', 'better_model': 'TIE',
            'test_method': 'N/A'
        }
 
    if n_dis < 25:
        p_value = 2 * min(
            stats.binom.cdf(min(b_val, c_val), n_dis, 0.5),
            stats.binom.cdf(min(b_val, c_val) - 1, n_dis, 0.5) if min(b_val, c_val) > 0 else 0
        )
        p_value = min(p_value, 1.0)
        chi_sq  = (abs(b_val - c_val) - 1) ** 2 / n_dis
        method  = 'Exact binomial'
    else:
        chi_sq  = (abs(b_val - c_val) - 1) ** 2 / n_dis
        p_value = 1 - stats.chi2.cdf(chi_sq, df=1)
        method  = 'Asymptotic (continuity correction)'
 
    if p_value < 0.001:   sig = '*** (p < 0.001)'
    elif p_value < 0.01:  sig = '** (p < 0.01)'
    elif p_value < 0.05:  sig = '* (p < 0.05)'
    else:                 sig = 'ns (not significant)'
 
    better = 'Model A' if b_val > c_val else ('Model B' if c_val > b_val else 'TIE')
 
    return {
        'b': b_val, 'c': c_val,
        'both_correct': both_correct, 'both_wrong': both_wrong,
        'n_disagreements': n_dis,
        'chi_square': chi_sq, 'p_value': p_value,
        'significance': sig, 'better_model': better,
        'test_method': method
    }
 
 
def get_sentence_correctness(y_true, y_pred):
    return [all(t == p for t, p in zip(tl, pl)) for tl, pl in zip(y_true, y_pred)]
 
 
def main():
    print("="*70)
    print("  McNEMAR'S SIGNIFICANCE TEST")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*70)
 
    print("\nLoading held-out naturalistic test set...")
    df_holdout = pd.read_pickle('data/test_holdout/naturalistic_bio.pkl')
    print(f"   Total samples: {len(df_holdout)}")
 
    y_true      = df_holdout['labels'].tolist()
    tokens_list = df_holdout['tokens'].tolist()
 
    print("\nExtracting features...")
 
    print("   Features CRF Murni...")
    X_pure, _ = features_v1.dataset_to_features(
        df_holdout, use_regex_features=False, verbose=False
    )
 
    print("   Features Hybrid CRF...")
    X_hybrid, _ = features_v2.dataset_to_features_v2(
        df_holdout, use_regex_features=True, use_gazetteer=True, verbose=False
    )
 
    print("\nGenerating predictions...")
    predictions = {}
 
    print("   CRF Murni...")
    with open('models/crf_pure.pkl', 'rb') as f:
        crf_pure = pickle.load(f)
    predictions['CRF Murni'] = crf_pure.predict(X_pure)
 
    print("   Hybrid CRF...")
    with open('models/hybrid_crf_v2.pkl', 'rb') as f:
        crf_hybrid = pickle.load(f)
    predictions['Hybrid CRF'] = crf_hybrid.predict(X_hybrid)
 
    print("   HMM Murni...")
    try:
        with open('models/hmm_pure.pkl', 'rb') as f:
            hmm_pure = pickle.load(f)
        predictions['HMM Murni'] = [hmm_pure.predict(t) for t in tokens_list]
    except Exception as e:
        print(f"      HMM Murni skip: {e}")
 
    print("   Hybrid HMM...")
    try:
        with open('models/hybrid_hmm.pkl', 'rb') as f:
            hybrid_hmm = pickle.load(f)
        predictions['Hybrid HMM'] = [hybrid_hmm.predict(t) for t in tokens_list]
    except Exception as e:
        print(f"      Hybrid HMM skip: {e}")
 
    print(f"\n   Models loaded: {list(predictions.keys())}")
 
    print("\nComputing sentence-level correctness...")
    correctness = {}
    for name, preds in predictions.items():
        correctness[name] = get_sentence_correctness(y_true, preds)
        n_correct = sum(correctness[name])
        acc = n_correct / len(correctness[name]) * 100
        print(f"   {name:<18}: {n_correct}/{len(correctness[name])} = {acc:.1f}%")
 
    print("\n" + "="*70)
    print("  PAIRWISE McNEMAR'S TESTS (Sentence-Level)")
    print("="*70)
 
    pairs = [
        ('Hybrid CRF', 'CRF Murni'),
        ('Hybrid CRF', 'Hybrid HMM'),
        ('CRF Murni',  'HMM Murni'),
        ('Hybrid HMM', 'HMM Murni'),
        ('Hybrid CRF', 'HMM Murni'),
    ]
 
    results = {}
 
    for model_a, model_b in pairs:
        if model_a not in correctness or model_b not in correctness:
            print(f"\n  Skip: {model_a} vs {model_b} (model not available)")
            continue
 
        print(f"\n  {model_a} vs {model_b}")
        print("  " + "-"*64)
 
        res = mcnemars_test(correctness[model_a], correctness[model_b])
 
        print(f"     Both correct        : {res['both_correct']}")
        print(f"     Both wrong          : {res['both_wrong']}")
        print(f"     {model_a} only correct : {res['b']} (b)")
        print(f"     {model_b} only correct : {res['c']} (c)")
        print(f"     Test method         : {res['test_method']}")
        print(f"     Chi-square          : {res['chi_square']:.4f}")
        print(f"     p-value             : {res['p_value']:.6f}")
        print(f"     Significance        : {res['significance']}")
 
        if res['better_model'] == 'Model A':
            winner = model_a
        elif res['better_model'] == 'Model B':
            winner = model_b
        else:
            winner = 'TIE'
 
        if res['p_value'] < 0.05:
            print(f"     Winner              : {winner}")
            print(f"     Interpretasi        : Perbedaan SIGNIFIKAN secara statistik")
        else:
            print(f"     Interpretasi        : Perbedaan TIDAK signifikan")
 
        results[f"{model_a}_vs_{model_b}"] = {
            'model_a': model_a, 'model_b': model_b, 'winner': winner, **res
        }
 
    print("\n" + "="*70)
    print("  SUMMARY TABLE")
    print("="*70)
    print(f"\n  {'Comparison':<35} {'Chi-sq':>10} {'p-value':>12} {'Sig.':>10}")
    print("  " + "-"*68)
    for key, res in results.items():
        comp = f"{res['model_a']} vs {res['model_b']}"
        sig  = res['significance'].split(' ')[0]
        print(f"  {comp:<35} {res['chi_square']:>10.4f} {res['p_value']:>12.6f} {sig:>10}")
    print("  " + "-"*68)
    print("  Sig.: *** p<0.001, ** p<0.01, * p<0.05, ns = not significant")
 
    print("\n" + "="*70)
    print("  CONCLUSION: Hybrid CRF vs CRF Murni")
    print("="*70)
 
    key = "Hybrid CRF_vs_CRF Murni"
    if key in results:
        r = results[key]
        if r['p_value'] < 0.05 and r['better_model'] == 'Model A':
            print(f"\n  Hybrid CRF MENGALAHKAN CRF Murni secara SIGNIFIKAN")
            print(f"  p-value = {r['p_value']:.6f} ({r['significance']})")
            print(f"  Hybrid CRF benar di {r['b']} sampel yang CRF Murni salah")
            print(f"  CRF Murni benar di {r['c']} sampel yang Hybrid CRF salah")
            print(f"\n  Klaim ilmiah:")
            print(f"  Hybrid CRF dengan knowledge injection framework")
            print(f"  menunjukkan performa yang SIGNIFIKAN LEBIH BAIK")
            print(f"  dari CRF Murni pada held-out naturalistic test set.")
 
    os.makedirs('evaluation', exist_ok=True)
    out = 'evaluation/mcnemars_test_results.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({
            'test': "McNemar's significance test",
            'test_set': 'held-out naturalistic (1000 samples)',
            'evaluation_level': 'sentence-level',
            'computed_at': datetime.now().isoformat(),
            'results': results,
            'accuracies': {
                n: sum(c) / len(c) for n, c in correctness.items()
            }
        }, f, indent=2, ensure_ascii=False)
 
    print(f"\n  Results saved: {out}")
    print("="*70)
 
 
if __name__ == "__main__":
    main()