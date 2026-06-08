"""Cek struktur HMM model yang di-save"""
import pickle

print("="*60)
print("HMM MURNI Structure:")
print("="*60)
with open('models/hmm_pure.pkl', 'rb') as f:
    hmm = pickle.load(f)

print(f"Type: {type(hmm).__name__}")
if isinstance(hmm, dict):
    print(f"Keys: {list(hmm.keys())}")
    for k, v in hmm.items():
        print(f"  {k}: {type(v).__name__}", end="")
        if hasattr(v, 'shape'):
            print(f" shape={v.shape}")
        elif isinstance(v, dict):
            print(f" dict with {len(v)} keys, first 3: {list(v.keys())[:3]}")
        elif isinstance(v, list):
            print(f" list len={len(v)}")
        else:
            print(f" value={v}")

print("\n" + "="*60)
print("HYBRID HMM Structure:")
print("="*60)
with open('models/hybrid_hmm.pkl', 'rb') as f:
    hybrid_hmm = pickle.load(f)

print(f"Type: {type(hybrid_hmm).__name__}")
if isinstance(hybrid_hmm, dict):
    print(f"Keys: {list(hybrid_hmm.keys())}")
    for k, v in hybrid_hmm.items():
        print(f"  {k}: {type(v).__name__}", end="")
        if hasattr(v, 'shape'):
            print(f" shape={v.shape}")
        elif isinstance(v, dict):
            print(f" dict with {len(v)} keys, first 3: {list(v.keys())[:3]}")
        elif isinstance(v, list):
            print(f" list len={len(v)}")
        else:
            print(f" value={v}")