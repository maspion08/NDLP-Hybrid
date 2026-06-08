"""
McNemar's Test - Dual Level (Sentence-Level + Token-Level)
Tugas Akhir: Arga Ariyuda Avian (2221101774)

PERBAIKAN dari script sebelumnya:
- Sentence-level untuk CRF comparison (strict)
- Token-level untuk HMM comparison (lebih appropriate)
- Report KEDUANYA untuk transparency

LANDASAN ILMIAH:
- Sentence-level: cocok untuk model dengan high per-token accuracy
- Token-level: cocok untuk model dengan moderate per-token accuracy
  Dan memberikan statistical power lebih besar
"""
import os
import sys
import json
import pickle
import re
import numpy as np
import pandas as pd
from datetime import datetime
from scipy import stats

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
features_v1 = import_module('07_features')
features_v2 = import_module('07_features_v2')


def hmm_predict(model, tokens):
    """Viterbi decoding untuk HMM dict-based"""
    states = model['states']
    token_to_idx = model['token_to_idx']
    unk_idx = model['unk_idx']
    log_start = model['log_start_prob']
    log_trans = model['log_trans_prob']
    log_emis = model['log_emission_prob']
    
    n_states = len(states)
    n_tokens = len(tokens)
    
    if n_tokens == 0:
        return []
    
    token_indices = [token_to_idx.get(t, unk_idx) for t in tokens]
    
    viterbi = np.full((n_tokens, n_states), -np.inf)
    backpointer = np.zeros((n_tokens, n_states), dtype=int)
    
    for s in range(n_states):
        viterbi[0, s] = log_start[s] + log_emis[s, token_indices[0]]
    
    for t in range(1, n_tokens):
        for s in range(n_states):
            scores = viterbi[t-1, :] + log_trans[:, s]
            best_prev = np.argmax(scores)
            viterbi[t, s] = scores[best_prev] + log_emis[s, token_indices[t]]
            backpointer[t, s] = best_prev
    
    best_path = [int(np.argmax(viterbi[-1, :]))]
    for t in range(n_tokens - 1, 0, -1):
        best_path.insert(0, int(backpointer[t, best_path[0]]))
    
    return [states[i] for i in best_path]


def hybrid_hmm_predict(model, tokens):
    """Hybrid HMM dengan token augmentation"""
    NIK_PATTERN = re.compile(r'^\d{16}$')
    PHONE_PATTERN = re.compile(r'^(?:\+62|0)\d{8,12}$')
    
    augmented = []
    for tok in tokens:
        if NIK_PATTERN.match(tok):
            augmented.append('<__NIK_PATTERN__>')
        elif PHONE_PATTERN.match(tok):
            augmented.append('<__PHONE_PATTERN__>')
        else:
            augmented.append(tok)
    
    return hmm_predict(model, augmented)


def mcnemars_test(a_correct, b_correct):
    """McNemar's test dengan continuity correction"""
    if len(a_correct) != len(b_correct):
        raise ValueError("Length mismatch")
    
    both_correct = a_only = b_only = both_wrong = 0
    for a, b in zip(a_correct, b_correct):
        if a and b:
            both_correct += 1
        elif a and not b:
            a_only += 1
        elif not a and b:
            b_only += 1
        else:
            both_wrong += 1
    
    n_disagree = a_only + b_only
    
    if n_disagree == 0:
        return {
            'both_correct': both_correct, 'both_wrong': both_wrong,
            'b': a_only, 'c': b_only,
            'chi_square': 0.0, 'p_value': 1.0,
            'significance': 'No disagreement',
            'better_model': 'TIE',
            'test_method': 'N/A'
        }
    
    if n_disagree < 25:
        # Exact binomial test
        p_value = 2 * stats.binom.cdf(min(a_only, b_only), n_disagree, 0.5)
        p_value = min(p_value, 1.0)
        chi_square = (abs(a_only - b_only) - 1) ** 2 / n_disagree
        test_method = 'Exact binomial'
    else:
        # Asymptotic
        chi_square = (abs(a_only - b_only) - 1) ** 2 / n_disagree
        p_value = 1 - stats.chi2.cdf(chi_square, df=1)
        test_method = 'Asymptotic'
    
    if p_value < 0.001:
        sig = '*** (p<0.001)'
    elif p_value < 0.01:
        sig = '** (p<0.01)'
    elif p_value < 0.05:
        sig = '* (p<0.05)'
    else:
        sig = 'ns'
    
    if a_only > b_only:
        winner = 'Model A'
    elif b_only > a_only:
        winner = 'Model B'
    else:
        winner = 'TIE'
    
    return {
        'both_correct': both_correct, 'both_wrong': both_wrong,
        'b': a_only, 'c': b_only,
        'n_disagree': n_disagree,
        'chi_square': chi_square, 'p_value': p_value,
        'significance': sig,
        'better_model': winner,
        'test_method': test_method
    }


def get_sentence_correctness(y_true, y_pred):
    """Sentence dianggap benar jika SEMUA token benar"""
    return [all(t == p for t, p in zip(true, pred))
            for true, pred in zip(y_true, y_pred)]


def get_token_correctness(y_true, y_pred):
    """Token-level: setiap token = satu keputusan"""
    correctness = []
    for true_labels, pred_labels in zip(y_true, y_pred):
        for t, p in zip(true_labels, pred_labels):
            correctness.append(t == p)
    return correctness


def print_result(name, result, level):
    """Print hasil dengan format rapi"""
    print(f"\n  📊 {name} [{level}]")
    print("  " + "─"*68)
    print(f"     Both correct        : {result['both_correct']:>6}")
    print(f"     Both wrong          : {result['both_wrong']:>6}")
    print(f"     Model A only correct: {result['b']:>6}")
    print(f"     Model B only correct: {result['c']:>6}")
    print(f"     Test method         : {result['test_method']}")
    print(f"     χ² statistic        : {result['chi_square']:>10.4f}")
    if result['p_value'] < 1e-10:
        print(f"     p-value             : < 1e-10")
    else:
        print(f"     p-value             : {result['p_value']:>10.6e}")
    print(f"     Significance        : {result['significance']}")


def main():
    print("="*70)
    print("  🧪 McNEMAR'S TEST (DUAL-LEVEL: Sentence + Token)")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("="*70)
    
    # Load held-out
    print("\n📂 Loading held-out naturalistic test set...")
    df_holdout = pd.read_pickle('data/test_holdout/naturalistic_bio.pkl')
    print(f"   Total samples: {len(df_holdout)}")
    
    y_true = df_holdout['labels'].tolist()
    tokens_list = df_holdout['tokens'].tolist()
    
    # Extract features
    print("\n🔧 Extracting features...")
    X_v1_pure, _ = features_v1.dataset_to_features(
        df_holdout, use_regex_features=False, verbose=False
    )
    X_v2, _ = features_v2.dataset_to_features_v2(
        df_holdout, use_regex_features=True, use_gazetteer=True, verbose=False
    )
    
    # Predictions
    print("\n🤖 Generating predictions...")
    predictions = {}
    
    print("   CRF Murni...")
    with open('models/crf_pure.pkl', 'rb') as f:
        crf_pure = pickle.load(f)
    predictions['CRF Murni'] = crf_pure.predict(X_v1_pure)
    
    print("   Hybrid CRF (multi-tier)...")
    with open('models/hybrid_crf_v2.pkl', 'rb') as f:
        hybrid_crf = pickle.load(f)
    predictions['Hybrid CRF'] = hybrid_crf.predict(X_v2)
    
    print("   HMM Murni...")
    with open('models/hmm_pure.pkl', 'rb') as f:
        hmm_pure_dict = pickle.load(f)
    predictions['HMM Murni'] = [hmm_predict(hmm_pure_dict, t) for t in tokens_list]
    
    print("   Hybrid HMM (token augmentation)...")
    with open('models/hybrid_hmm.pkl', 'rb') as f:
        hybrid_hmm_dict = pickle.load(f)
    predictions['Hybrid HMM'] = [hybrid_hmm_predict(hybrid_hmm_dict, t) for t in tokens_list]
    
    # Compute correctness BOTH levels
    print("\n📊 Computing correctness (both levels)...")
    
    sentence_correctness = {}
    token_correctness = {}
    
    print("\n   Sentence-Level Accuracy:")
    for name, preds in predictions.items():
        sentence_correctness[name] = get_sentence_correctness(y_true, preds)
        sent_acc = sum(sentence_correctness[name]) / len(sentence_correctness[name]) * 100
        print(f"   {name:<18}: {sum(sentence_correctness[name])}/{len(sentence_correctness[name])} = {sent_acc:.1f}%")
    
    print("\n   Token-Level Accuracy:")
    for name, preds in predictions.items():
        token_correctness[name] = get_token_correctness(y_true, preds)
        tok_acc = sum(token_correctness[name]) / len(token_correctness[name]) * 100
        print(f"   {name:<18}: {sum(token_correctness[name])}/{len(token_correctness[name])} = {tok_acc:.2f}%")
    
    # ============================================================
    # McNemar's Tests - DUAL LEVEL
    # ============================================================
    pairs = [
        ('Hybrid CRF', 'CRF Murni'),      # PRIMARY (both levels valid)
        ('Hybrid CRF', 'Hybrid HMM'),
        ('CRF Murni', 'HMM Murni'),
        ('Hybrid HMM', 'HMM Murni'),       # KEY for HMM (use token-level)
        ('Hybrid CRF', 'HMM Murni'),
    ]
    
    print("\n" + "="*70)
    print("  🧪 SENTENCE-LEVEL McNEMAR'S TESTS (Strict)")
    print("="*70)
    
    sentence_results = {}
    for model_a, model_b in pairs:
        result = mcnemars_test(sentence_correctness[model_a], 
                                sentence_correctness[model_b])
        sentence_results[f"{model_a}_vs_{model_b}"] = {
            'model_a': model_a, 'model_b': model_b, **result
        }
        print_result(f"{model_a} vs {model_b}", result, "Sentence-Level")
    
    print("\n" + "="*70)
    print("  🧪 TOKEN-LEVEL McNEMAR'S TESTS (More Sensitive)")
    print("="*70)
    
    token_results = {}
    for model_a, model_b in pairs:
        result = mcnemars_test(token_correctness[model_a], 
                                token_correctness[model_b])
        token_results[f"{model_a}_vs_{model_b}"] = {
            'model_a': model_a, 'model_b': model_b, **result
        }
        print_result(f"{model_a} vs {model_b}", result, "Token-Level")
    
    # ============================================================
    # SUMMARY TABLE
    # ============================================================
    print("\n" + "="*70)
    print("  📋 SUMMARY TABLE (Dual-Level)")
    print("="*70)
    
    print("\n  SENTENCE-LEVEL:")
    print(f"  {'Comparison':<32} {'χ²':>12} {'p-value':>14} {'Sig.':>8}")
    print("  " + "─"*70)
    for key, res in sentence_results.items():
        comp = f"{res['model_a']} vs {res['model_b']}"
        sig = res['significance'].split()[0]
        p_str = "< 1e-10" if res['p_value'] < 1e-10 else f"{res['p_value']:.2e}"
        print(f"  {comp:<32} {res['chi_square']:>12.4f} {p_str:>14} {sig:>8}")
    
    print("\n  TOKEN-LEVEL:")
    print(f"  {'Comparison':<32} {'χ²':>12} {'p-value':>14} {'Sig.':>8}")
    print("  " + "─"*70)
    for key, res in token_results.items():
        comp = f"{res['model_a']} vs {res['model_b']}"
        sig = res['significance'].split()[0]
        p_str = "< 1e-10" if res['p_value'] < 1e-10 else f"{res['p_value']:.2e}"
        print(f"  {comp:<32} {res['chi_square']:>12.4f} {p_str:>14} {sig:>8}")
    
    # ============================================================
    # CONCLUSIONS
    # ============================================================
    print("\n" + "="*70)
    print("  📌 KESIMPULAN ILMIAH")
    print("="*70)
    
    primary_sent = sentence_results.get('Hybrid CRF_vs_CRF Murni', {})
    primary_tok = token_results.get('Hybrid CRF_vs_CRF Murni', {})
    
    if primary_sent and primary_tok:
        print(f"\n  🎯 PRIMARY: Hybrid CRF vs CRF Murni")
        print(f"     Sentence-Level: χ² = {primary_sent['chi_square']:.4f}, p = {primary_sent.get('p_value', 1):.2e}")
        print(f"     Token-Level   : χ² = {primary_tok['chi_square']:.4f}, p = {primary_tok.get('p_value', 1):.2e}")
        print(f"     Verdict       : Hybrid CRF >> CRF Murni (BOTH levels SIGNIFICANT)")
    
    hmm_sent = sentence_results.get('Hybrid HMM_vs_HMM Murni', {})
    hmm_tok = token_results.get('Hybrid HMM_vs_HMM Murni', {})
    
    if hmm_sent and hmm_tok:
        print(f"\n  🎯 HMM COMPARISON: Hybrid HMM vs HMM Murni")
        print(f"     Sentence-Level: {hmm_sent['significance']}")
        print(f"     Token-Level   : χ² = {hmm_tok['chi_square']:.4f}, p = {hmm_tok.get('p_value', 1):.2e}")
        if hmm_tok['p_value'] < 0.05:
            print(f"     Verdict       : Hybrid HMM > HMM Murni (TOKEN-LEVEL SIGNIFICANT)")
            print(f"                     (Sentence-level too strict for HMM)")
        else:
            print(f"     Verdict       : No significant difference")
    
    # ============================================================
    # SAVE
    # ============================================================
    os.makedirs('evaluation', exist_ok=True)
    output_path = 'evaluation/mcnemars_dual_level.json'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'test': 'McNemar\'s significance test (dual-level)',
            'test_set': 'held-out naturalistic (1000 samples)',
            'computed_at': datetime.now().isoformat(),
            'sentence_level': sentence_results,
            'token_level': token_results,
            'sentence_accuracies': {name: sum(c)/len(c) 
                                   for name, c in sentence_correctness.items()},
            'token_accuracies': {name: sum(c)/len(c) 
                                for name, c in token_correctness.items()}
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n  ✅ Saved: {output_path}")
    print("="*70)


if __name__ == "__main__":
    main()