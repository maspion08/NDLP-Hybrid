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
   → Rekomendasi McNemar's test sebagai standard untuk ML comparison

3. Salzberg (1997) - "On Comparing Classifiers: Pitfalls to Avoid 
   and a Recommended Approach"

PROSEDUR:
=========
Untuk setiap pasangan model, hitung:
- b = sampel yang Model A benar, Model B salah
- c = sampel yang Model A salah, Model B benar
- χ² = (|b - c| - 1)² / (b + c)
- p-value dari distribusi chi-square dengan df=1

INTERPRETASI:
=============
- p < 0.001 : Highly significant (***)
- p < 0.01  : Very significant (**)
- p < 0.05  : Significant (*)
- p >= 0.05 : Not significant (ns)

EVALUASI:
=========
Dilakukan pada Held-Out Naturalistic Set (1000 sampel)
karena ini adalah test set paling realistis (out-of-distribution).
"""
import os
import sys
import json
import pickle
import pandas as pd
from datetime import datetime
from scipy import stats
from collections import Counter

# Set encoding untuk Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
features_v1 = import_module('07_features')
features_v2 = import_module('07_features_v2')
evaluator = import_module('08_evaluator')


def mcnemars_test(model_a_correct, model_b_correct):
    """
    Compute McNemar's test statistic
    
    Args:
        model_a_correct: list of booleans, prediksi Model A benar/salah
        model_b_correct: list of booleans, prediksi Model B benar/salah
    
    Returns:
        dict dengan b, c, chi_square, p_value, significance
    """
    if len(model_a_correct) != len(model_b_correct):
        raise ValueError("Length mismatch")
    
    # Build contingency table
    both_correct = 0     # a
    a_correct_b_wrong = 0  # b
    a_wrong_b_correct = 0  # c
    both_wrong = 0       # d
    
    for a_corr, b_corr in zip(model_a_correct, model_b_correct):
        if a_corr and b_corr:
            both_correct += 1
        elif a_corr and not b_corr:
            a_correct_b_wrong += 1  # b
        elif not a_corr and b_corr:
            a_wrong_b_correct += 1  # c
        else:
            both_wrong += 1
    
    b = a_correct_b_wrong
    c = a_wrong_b_correct
    n_disagreements = b + c
    
    # McNemar's test dengan continuity correction
    if n_disagreements == 0:
        return {
            'b': b, 'c': c,
            'both_correct': both_correct,
            'both_wrong': both_wrong,
            'chi_square': 0.0,
            'p_value': 1.0,
            'significance': 'No disagreement',
            'better_model': 'TIE',
            'note': 'Both models perfectly agree on all samples'
        }
    
    # Use exact binomial test untuk small samples
    if n_disagreements < 25:
        # Exact binomial test (more accurate for small samples)
        # H0: b and c are equally likely
        p_value = 2 * min(
            stats.binom.cdf(min(b, c), n_disagreements, 0.5),
            stats.binom.cdf(min(b, c) - 1, n_disagreements, 0.5) if min(b, c) > 0 else 0
        )
        p_value = min(p_value, 1.0)
        chi_square = (abs(b - c) - 1) ** 2 / n_disagreements if n_disagreements > 0 else 0
        test_method = 'Exact binomial'
    else:
        # Asymptotic McNemar's chi-square test
        chi_square = (abs(b - c) - 1) ** 2 / n_disagreements
        p_value = 1 - stats.chi2.cdf(chi_square, df=1)
        test_method = 'Asymptotic (continuity correction)'
    
    # Determine significance level
    if p_value < 0.001:
        significance = '*** (p < 0.001)'
    elif p_value < 0.01:
        significance = '** (p < 0.01)'
    elif p_value < 0.05:
        significance = '* (p < 0.05)'
    else:
        significance = 'ns (not significant)'
    
    # Determine which model is better
    if b > c:
        better_model = 'Model A'
    elif c > b:
        better_model = 'Model B'
    else:
        better_model = 'TIE'
    
    return {
        'b': b, 'c': c,
        'both_correct': both_correct,
        'both_wrong': both_wrong,
        'n_disagreements': n_disagreements,
        'chi_square': chi_square,
        'p_value': p_value,
        'significance': significance,
        'better_model': better_model,
        'test_method': test_method
    }


def get_sentence_correctness(y_true, y_pred):
    """
    Untuk setiap sentence, tentukan apakah prediksi BENAR atau SALAH.
    Definisi: sentence dianggap benar jika SEMUA token-nya benar.
    
    Alternative: bisa juga per-token, tapi per-sentence lebih
    konservatif dan sesuai dengan praktik NER.
    """
    correctness = []
    for true_labels, pred_labels in zip(y_true, y_pred):
        is_correct = all(t == p for t, p in zip(true_labels, pred_labels))
        correctness.append(is_correct)
    return correctness


def get_token_correctness(y_true, y_pred):
    """
    Untuk setiap TOKEN (bukan sentence), tentukan benar/salah.
    Ini memberikan sample size lebih besar untuk statistical test.
    """
    correctness = []
    for true_labels, pred_labels in zip(y_true, y_pred):
        for t, p in zip(true_labels, pred_labels):
            correctness.append(t == p)
    return correctness


def predict_with_model(model_path, X):
    """Load model dan predict"""
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model.predict(X)


def main():
    print("="*70)
    print("  🧪 McNEMAR'S SIGNIFICANCE TEST")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*70)
    
    # ============================================================
    # Load Held-Out Test Set (most realistic)
    # ============================================================
    print("\n📂 Loading held-out naturalistic test set...")
    df_holdout = pd.read_pickle('data/test_holdout/naturalistic_bio.pkl')
    print(f"   Total samples: {len(df_holdout)}")
    
    y_true = df_holdout['labels'].tolist()
    tokens_list = df_holdout['tokens'].tolist()
    
    # ============================================================
    # Extract features untuk semua model
    # ============================================================
    print("\n🔧 Extracting features...")
    
    # Features v1 (untuk CRF Murni)
    print("   v1 features (CRF Murni)...")
    X_v1_pure, _ = features_v1.dataset_to_features(
        df_holdout, use_regex_features=False, verbose=False
    )
    
    # Features v1 dengan regex (untuk Hybrid CRF v1 lama - tidak dipakai)
    print("   v1 features with regex (legacy hybrid)...")
    X_v1_hybrid, _ = features_v1.dataset_to_features(
        df_holdout, use_regex_features=True, verbose=False
    )
    
    # Features v2 (untuk Hybrid CRF current - WINNER)
    print("   v2 features (Hybrid CRF current)...")
    X_v2, _ = features_v2.dataset_to_features_v2(
        df_holdout, use_regex_features=True, use_gazetteer=True, verbose=False
    )
    
    # ============================================================
    # Get predictions dari semua model
    # ============================================================
    print("\n🤖 Generating predictions from all models...")
    
    predictions = {}
    
    # CRF Murni
    print("   CRF Murni...")
    predictions['CRF Murni'] = predict_with_model('models/crf_pure.pkl', X_v1_pure)
    
    # Hybrid CRF (winner)
    print("   Hybrid CRF (multi-tier)...")
    predictions['Hybrid CRF'] = predict_with_model('models/hybrid_crf_v2.pkl', X_v2)
    
    # HMM Murni - perlu handle khusus karena pakai vocabulary
    print("   HMM Murni...")
    try:
        with open('models/hmm_pure.pkl', 'rb') as f:
            hmm_pure = pickle.load(f)
        predictions['HMM Murni'] = [hmm_pure.predict(t) for t in tokens_list]
    except Exception as e:
        print(f"      ⚠️  HMM Murni skip: {e}")
    
    # Hybrid HMM
    print("   Hybrid HMM...")
    try:
        with open('models/hybrid_hmm.pkl', 'rb') as f:
            hybrid_hmm = pickle.load(f)
        predictions['Hybrid HMM'] = [hybrid_hmm.predict(t) for t in tokens_list]
    except Exception as e:
        print(f"      ⚠️  Hybrid HMM skip: {e}")
    
    print(f"\n   ✅ Models loaded: {list(predictions.keys())}")
    
    # ============================================================
    # Get correctness per sentence
    # ============================================================
    print("\n📊 Computing correctness per sentence...")
    
    correctness = {}
    for model_name, preds in predictions.items():
        correctness[model_name] = get_sentence_correctness(y_true, preds)
        n_correct = sum(correctness[model_name])
        accuracy = n_correct / len(correctness[model_name]) * 100
        print(f"   {model_name:<18}: {n_correct}/{len(correctness[model_name])} = {accuracy:.1f}%")
    
    # ============================================================
    # McNemar's Tests
    # ============================================================
    print("\n" + "="*70)
    print("  🧪 PAIRWISE McNEMAR'S TESTS (Sentence-Level)")
    print("="*70)
    
    # Define important pairs to test
    pairs = [
        ('Hybrid CRF', 'CRF Murni'),      # PRIMARY: validate hybrid > pure
        ('Hybrid CRF', 'Hybrid HMM'),      # Validate CRF > HMM
        ('CRF Murni', 'HMM Murni'),        # Pure CRF > Pure HMM
        ('Hybrid HMM', 'HMM Murni'),       # Hybrid helps HMM
        ('Hybrid CRF', 'HMM Murni'),       # Best vs worst
    ]
    
    results = {}
    
    for model_a_name, model_b_name in pairs:
        if model_a_name not in correctness or model_b_name not in correctness:
            print(f"\n  ⚠️  Skip: {model_a_name} vs {model_b_name} (model not available)")
            continue
        
        print(f"\n  📊 {model_a_name} vs {model_b_name}")
        print("  " + "─"*64)
        
        result = mcnemars_test(
            correctness[model_a_name],
            correctness[model_b_name]
        )
        
        # Display result
        print(f"     Both correct        : {result['both_correct']}")
        print(f"     Both wrong          : {result['both_wrong']}")
        print(f"     {model_a_name} only correct  : {result['b']} (b)")
        print(f"     {model_b_name} only correct  : {result['c']} (c)")
        print(f"     Test method         : {result['test_method']}")
        print(f"     χ² statistic        : {result['chi_square']:.4f}")
        print(f"     p-value             : {result['p_value']:.6f}")
        print(f"     Significance        : {result['significance']}")
        
        # Determine winner
        if result['better_model'] == 'Model A':
            winner = model_a_name
            print(f"     🏆 Winner           : {winner}")
        elif result['better_model'] == 'Model B':
            winner = model_b_name
            print(f"     🏆 Winner           : {winner}")
        else:
            winner = 'TIE'
            print(f"     🤝 Result           : TIE")
        
        # Interpretation
        is_significant = result['p_value'] < 0.05
        if is_significant:
            print(f"     💡 Interpretation   : Perbedaan SIGNIFIKAN secara statistik")
        else:
            print(f"     💡 Interpretation   : Perbedaan TIDAK signifikan")
        
        results[f"{model_a_name}_vs_{model_b_name}"] = {
            'model_a': model_a_name,
            'model_b': model_b_name,
            'winner': winner,
            **result
        }
    
    # ============================================================
    # Summary Table
    # ============================================================
    print("\n" + "="*70)
    print("  📋 SUMMARY TABLE")
    print("="*70)
    print()
    print(f"  {'Comparison':<35} {'χ²':>10} {'p-value':>12} {'Sig.':>10}")
    print("  " + "─"*68)
    
    for key, res in results.items():
        comp = f"{res['model_a']} vs {res['model_b']}"
        sig_short = res['significance'].split(' ')[0]
        print(f"  {comp:<35} {res['chi_square']:>10.4f} {res['p_value']:>12.6f} {sig_short:>10}")
    
    print("  " + "─"*68)
    print("  Sig. legend: *** p<0.001, ** p<0.01, * p<0.05, ns = not significant")
    
    # ============================================================
    # Conclusion
    # ============================================================
    print("\n" + "="*70)
    print("  📌 CONCLUSIONS")
    print("="*70)
    
    # Primary comparison: Hybrid CRF vs CRF Murni
    primary_key = "Hybrid CRF_vs_CRF Murni"
    if primary_key in results:
        primary = results[primary_key]
        print(f"\n  🎯 PRIMARY COMPARISON: Hybrid CRF vs CRF Murni")
        
        if primary['p_value'] < 0.05:
            if primary['better_model'] == 'Model A':  # Hybrid CRF
                print(f"     ✅ Hybrid CRF MENGALAHKAN CRF Murni secara SIGNIFIKAN")
                print(f"        p-value = {primary['p_value']:.6f}")
                print(f"        Disagreements: Hybrid CRF benar di {primary['b']} sampel,")
                print(f"                       CRF Murni benar di {primary['c']} sampel")
                print(f"     ")
                print(f"     💪 Klaim ilmiah:")
                print(f"        \"Hybrid CRF dengan kerangka Regex-as-a-Feature multi-")
                print(f"         tier menunjukkan performa yang SIGNIFIKAN LEBIH BAIK")
                print(f"         dari CRF Murni (p < {0.001 if primary['p_value'] < 0.001 else 0.01 if primary['p_value'] < 0.01 else 0.05}) pada held-out naturalistic")
                print(f"         test set.\"")
            else:
                print(f"     ❌ CRF Murni menang signifikan")
        else:
            print(f"     ⚠️  Perbedaan TIDAK signifikan secara statistik")
            print(f"        p-value = {primary['p_value']:.6f}")
    
    # ============================================================
    # Save Results
    # ============================================================
    os.makedirs('evaluation', exist_ok=True)
    output_path = 'evaluation/mcnemars_test_results.json'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'test': 'McNemar\'s significance test',
            'test_set': 'held-out naturalistic (1000 samples)',
            'evaluation_level': 'sentence-level (entire sentence must be correct)',
            'computed_at': datetime.now().isoformat(),
            'results': results,
            'accuracies': {
                name: sum(corr) / len(corr) 
                for name, corr in correctness.items()
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n  ✅ Results saved: {output_path}")
    print("="*70)


if __name__ == "__main__":
    main()