"""
McNemar's Test dengan support untuk HMM custom (dict-based)
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Update dari script 33: tambah HMM prediction support
"""
import os
import sys
import json
import pickle
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


def hmm_predict(hmm_model, tokens):
    """
    Viterbi decoding untuk HMM yang di-save sebagai dict.
    
    Args:
        hmm_model: dict dengan keys (states, vocab, token_to_idx, 
                   log_start_prob, log_trans_prob, log_emission_prob)
        tokens: list of tokens dalam satu sentence
    
    Returns:
        list of labels (BIO tags) hasil Viterbi decoding
    """
    states = hmm_model['states']
    state_to_idx = hmm_model['state_to_idx']
    token_to_idx = hmm_model['token_to_idx']
    unk_idx = hmm_model['unk_idx']
    log_start = hmm_model['log_start_prob']
    log_trans = hmm_model['log_trans_prob']
    log_emis = hmm_model['log_emission_prob']
    
    n_states = len(states)
    n_tokens = len(tokens)
    
    if n_tokens == 0:
        return []
    
    # Map tokens to indices, use UNK for unknown
    token_indices = []
    for tok in tokens:
        idx = token_to_idx.get(tok, unk_idx)
        token_indices.append(idx)
    
    # Viterbi in log-space
    # viterbi[t, s] = max log-probability of best path ending at state s at time t
    viterbi = np.full((n_tokens, n_states), -np.inf)
    backpointer = np.zeros((n_tokens, n_states), dtype=int)
    
    # Initialize t=0
    for s in range(n_states):
        viterbi[0, s] = log_start[s] + log_emis[s, token_indices[0]]
    
    # Recursion t=1..n
    for t in range(1, n_tokens):
        for s in range(n_states):
            # Find best previous state
            scores = viterbi[t-1, :] + log_trans[:, s]
            best_prev = np.argmax(scores)
            viterbi[t, s] = scores[best_prev] + log_emis[s, token_indices[t]]
            backpointer[t, s] = best_prev
    
    # Backtrack
    best_path = [int(np.argmax(viterbi[-1, :]))]
    for t in range(n_tokens - 1, 0, -1):
        best_path.insert(0, int(backpointer[t, best_path[0]]))
    
    # Convert indices to state labels
    return [states[i] for i in best_path]


def hybrid_hmm_predict(hmm_model, tokens):
    """
    Prediksi untuk Hybrid HMM: pre-process tokens dulu (token augmentation),
    baru Viterbi decoding.
    """
    import re
    
    # Token augmentation: replace NIK/PHONE patterns
    NIK_PATTERN = re.compile(r'^\d{16}$')
    PHONE_PATTERN = re.compile(r'^(?:\+62|0)\d{8,12}$')
    
    augmented_tokens = []
    for tok in tokens:
        if NIK_PATTERN.match(tok):
            augmented_tokens.append('<__NIK_PATTERN__>')
        elif PHONE_PATTERN.match(tok):
            augmented_tokens.append('<__PHONE_PATTERN__>')
        else:
            augmented_tokens.append(tok)
    
    return hmm_predict(hmm_model, augmented_tokens)


def mcnemars_test(model_a_correct, model_b_correct):
    """Compute McNemar's test"""
    if len(model_a_correct) != len(model_b_correct):
        raise ValueError("Length mismatch")
    
    both_correct = a_correct_b_wrong = a_wrong_b_correct = both_wrong = 0
    
    for a_corr, b_corr in zip(model_a_correct, model_b_correct):
        if a_corr and b_corr:
            both_correct += 1
        elif a_corr and not b_corr:
            a_correct_b_wrong += 1
        elif not a_corr and b_corr:
            a_wrong_b_correct += 1
        else:
            both_wrong += 1
    
    b = a_correct_b_wrong
    c = a_wrong_b_correct
    n_disagreements = b + c
    
    if n_disagreements == 0:
        return {
            'b': b, 'c': c,
            'both_correct': both_correct,
            'both_wrong': both_wrong,
            'chi_square': 0.0,
            'p_value': 1.0,
            'significance': 'No disagreement',
            'better_model': 'TIE',
            'test_method': 'N/A'
        }
    
    if n_disagreements < 25:
        # Exact binomial test
        p_value = 2 * stats.binom.cdf(min(b, c), n_disagreements, 0.5)
        p_value = min(p_value, 1.0)
        chi_square = (abs(b - c) - 1) ** 2 / n_disagreements
        test_method = 'Exact binomial'
    else:
        chi_square = (abs(b - c) - 1) ** 2 / n_disagreements
        p_value = 1 - stats.chi2.cdf(chi_square, df=1)
        test_method = 'Asymptotic (continuity correction)'
    
    if p_value < 0.001:
        significance = '*** (p < 0.001)'
    elif p_value < 0.01:
        significance = '** (p < 0.01)'
    elif p_value < 0.05:
        significance = '* (p < 0.05)'
    else:
        significance = 'ns (not significant)'
    
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
    """Sentence-level correctness: semua token harus benar"""
    return [all(t == p for t, p in zip(true, pred)) 
            for true, pred in zip(y_true, y_pred)]


def main():
    print("="*70)
    print("  🧪 McNEMAR'S TEST (COMPLETE - dengan HMM Support)")
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
    
    # Get predictions
    print("\n🤖 Generating predictions...")
    predictions = {}
    
    # CRF Murni
    print("   CRF Murni...")
    with open('models/crf_pure.pkl', 'rb') as f:
        crf_pure = pickle.load(f)
    predictions['CRF Murni'] = crf_pure.predict(X_v1_pure)
    
    # Hybrid CRF
    print("   Hybrid CRF (multi-tier)...")
    with open('models/hybrid_crf_v2.pkl', 'rb') as f:
        hybrid_crf = pickle.load(f)
    predictions['Hybrid CRF'] = hybrid_crf.predict(X_v2)
    
    # HMM Murni (custom dict-based)
    print("   HMM Murni (custom dict)...")
    with open('models/hmm_pure.pkl', 'rb') as f:
        hmm_pure_dict = pickle.load(f)
    predictions['HMM Murni'] = [hmm_predict(hmm_pure_dict, t) 
                                 for t in tokens_list]
    
    # Hybrid HMM (dengan token augmentation)
    print("   Hybrid HMM (token augmentation)...")
    with open('models/hybrid_hmm.pkl', 'rb') as f:
        hybrid_hmm_dict = pickle.load(f)
    predictions['Hybrid HMM'] = [hybrid_hmm_predict(hybrid_hmm_dict, t) 
                                   for t in tokens_list]
    
    print(f"\n   ✅ All 4 models loaded: {list(predictions.keys())}")
    
    # Sentence-level correctness
    print("\n📊 Computing sentence-level correctness...")
    correctness = {}
    for name, preds in predictions.items():
        correctness[name] = get_sentence_correctness(y_true, preds)
        acc = sum(correctness[name]) / len(correctness[name]) * 100
        print(f"   {name:<18}: {sum(correctness[name])}/{len(correctness[name])} = {acc:.1f}%")
    
    # Pairwise tests
    print("\n" + "="*70)
    print("  🧪 PAIRWISE McNEMAR'S TESTS")
    print("="*70)
    
    pairs = [
        ('Hybrid CRF', 'CRF Murni'),
        ('Hybrid CRF', 'Hybrid HMM'),
        ('CRF Murni', 'HMM Murni'),
        ('Hybrid HMM', 'HMM Murni'),
        ('Hybrid CRF', 'HMM Murni'),
    ]
    
    results = {}
    
    for model_a, model_b in pairs:
        if model_a not in correctness or model_b not in correctness:
            continue
        
        print(f"\n  📊 {model_a} vs {model_b}")
        print("  " + "─"*64)
        
        result = mcnemars_test(correctness[model_a], correctness[model_b])
        
        print(f"     Both correct        : {result['both_correct']}")
        print(f"     Both wrong          : {result['both_wrong']}")
        print(f"     {model_a} only correct  : {result['b']}")
        print(f"     {model_b} only correct  : {result['c']}")
        print(f"     χ² statistic        : {result['chi_square']:.4f}")
        print(f"     p-value             : {result['p_value']:.6f}")
        print(f"     Significance        : {result['significance']}")
        
        if result['better_model'] == 'Model A':
            winner = model_a
        elif result['better_model'] == 'Model B':
            winner = model_b
        else:
            winner = 'TIE'
        print(f"     🏆 Winner           : {winner}")
        
        results[f"{model_a}_vs_{model_b}"] = {
            'model_a': model_a, 'model_b': model_b,
            'winner': winner, **result
        }
    
    # Summary
    print("\n" + "="*70)
    print("  📋 SUMMARY TABLE")
    print("="*70)
    print()
    print(f"  {'Comparison':<35} {'χ²':>10} {'p-value':>14} {'Sig.':>10}")
    print("  " + "─"*70)
    
    for key, res in results.items():
        comp = f"{res['model_a']} vs {res['model_b']}"
        sig_short = res['significance'].split(' ')[0]
        p_str = f"{res['p_value']:.2e}" if res['p_value'] > 0 else "< 1e-10"
        print(f"  {comp:<35} {res['chi_square']:>10.4f} {p_str:>14} {sig_short:>10}")
    
    print("  " + "─"*70)
    print("  *** p<0.001, ** p<0.01, * p<0.05, ns = not significant")
    
    # Save
    os.makedirs('evaluation', exist_ok=True)
    output_path = 'evaluation/mcnemars_test_complete.json'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'test': 'McNemar\'s significance test (complete)',
            'test_set': 'held-out naturalistic (1000 samples)',
            'evaluation_level': 'sentence-level',
            'computed_at': datetime.now().isoformat(),
            'results': results,
            'accuracies': {name: sum(corr)/len(corr) 
                          for name, corr in correctness.items()}
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n  ✅ Saved: {output_path}")
    print("="*70)


if __name__ == "__main__":
    main()