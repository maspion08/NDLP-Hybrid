"""Debug HMM prediction - cek apakah ada yang salah"""
import sys
import pickle
import re
import numpy as np
import pandas as pd

sys.path.insert(0, 'scripts')

# Load HMM
with open('models/hmm_pure.pkl', 'rb') as f:
    hmm_pure = pickle.load(f)

with open('models/hybrid_hmm.pkl', 'rb') as f:
    hybrid_hmm = pickle.load(f)

print("="*70)
print("HMM Murni Info:")
print(f"  States      : {hmm_pure['states']}")
print(f"  Vocab size  : {len(hmm_pure['vocab'])}")
print(f"  log_emis shape: {hmm_pure['log_emission_prob'].shape}")
print(f"  First 10 vocab: {hmm_pure['vocab'][:10]}")

print("\n" + "="*70)
print("Hybrid HMM Info:")
print(f"  States      : {hybrid_hmm['states']}")
print(f"  Vocab size  : {len(hybrid_hmm['vocab'])}")
print(f"  First 10 vocab: {hybrid_hmm['vocab'][:10]}")
print(f"  Contains __NIK_PATTERN__: {'<__NIK_PATTERN__>' in hybrid_hmm['vocab']}")
print(f"  Contains __PHONE_PATTERN__: {'<__PHONE_PATTERN__>' in hybrid_hmm['vocab']}")

# Cari special tokens di vocab
print("\n  Special tokens in Hybrid HMM vocab:")
for tok in hybrid_hmm['vocab']:
    if 'PATTERN' in tok or 'NIK' in tok.upper() or 'PHONE' in tok.upper():
        print(f"    - '{tok}'")

# ============================================================
# Test prediction on sample
# ============================================================
print("\n" + "="*70)
print("TEST: Load 1 sample dari holdout")
df = pd.read_pickle('data/test_holdout/naturalistic_bio.pkl')
sample = df.iloc[0]
tokens = sample['tokens']
labels = sample['labels']

print(f"\nTokens (first 15): {tokens[:15]}")
print(f"Labels (first 15): {labels[:15]}")

# Predict dengan HMM
def hmm_predict_debug(model, tokens):
    states = model['states']
    token_to_idx = model['token_to_idx']
    unk_idx = model['unk_idx']
    log_start = model['log_start_prob']
    log_trans = model['log_trans_prob']
    log_emis = model['log_emission_prob']
    
    n_states = len(states)
    n_tokens = len(tokens)
    
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


print("\nHMM Murni prediction (first 15 tokens):")
pred_pure = hmm_predict_debug(hmm_pure, tokens)
print(f"  {pred_pure[:15]}")

# Hybrid: dengan token augmentation
NIK_PAT = re.compile(r'^\d{16}$')
PHONE_PAT = re.compile(r'^(?:\+62|0)\d{8,12}$')

augmented = []
for tok in tokens:
    if NIK_PAT.match(tok):
        augmented.append('<__NIK_PATTERN__>')
    elif PHONE_PAT.match(tok):
        augmented.append('<__PHONE_PATTERN__>')
    else:
        augmented.append(tok)

print(f"\nAugmented tokens (first 15):")
print(f"  Original : {tokens[:15]}")
print(f"  Augmented: {augmented[:15]}")

print("\nHybrid HMM prediction (first 15 tokens):")
pred_hybrid = hmm_predict_debug(hybrid_hmm, augmented)
print(f"  {pred_hybrid[:15]}")

print(f"\nTrue labels (first 15):")
print(f"  {labels[:15]}")

# Check accuracy
correct_pure = sum(p == l for p, l in zip(pred_pure, labels))
correct_hybrid = sum(p == l for p, l in zip(pred_hybrid, labels))
print(f"\nToken-level accuracy:")
print(f"  HMM Murni : {correct_pure}/{len(labels)} = {correct_pure/len(labels)*100:.1f}%")
print(f"  Hybrid HMM: {correct_hybrid}/{len(labels)} = {correct_hybrid/len(labels)*100:.1f}%")

# Check if predictions are same
same = all(p == h for p, h in zip(pred_pure, pred_hybrid))
print(f"\nApakah prediksi HMM Murni dan Hybrid HMM IDENTIK?")
print(f"  {'YES (ANEH!)' if same else 'TIDAK (NORMAL)'}")