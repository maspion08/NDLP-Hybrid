"""
Test Models on Hard Adversarial - tanpa re-train
Lihat seberapa robust model existing terhadap challenging samples
"""
import os
import sys
import pickle
import pandas as pd
from importlib import import_module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

features_module = import_module('07_features')


def main():
    print("="*70)
    print("  🔥 STRESS TEST: Models on HARD ADVERSARIAL")
    print("="*70)
    
    df = pd.read_pickle('data/raw/hard_adversarial.pkl')
    print(f"\n📂 Loaded {len(df)} hard adversarial samples")
    
    # Need to BIO tag first (using simple ground truth)
    print("\n🏷️  BIO tagging hard adversarial...")
    bio_module = import_module('02_bio_tagger')
    
    # Process: for samples without PII, all O. For samples with PII, use tagger
    tagged_data = []
    tagger = bio_module.BioTagger()
    
    for _, row in df.iterrows():
        tokens, labels = tagger.tag_sample(
            payload=row['payload'],
            pii_data=row['pii_data'],
            format_type='narrative'  # treat as narrative
        )
        tagged_data.append({
            'tokens': tokens,
            'labels': labels,
            'payload': row['payload'],
            'pii_data': row['pii_data'],
            'category': row['category']
        })
    
    df_tagged = pd.DataFrame(tagged_data)
    
    # Save
    df_tagged.to_pickle('data/raw/hard_adversarial_bio.pkl')
    
    # Test each model
    models_to_test = {
        'Regex_Murni': 'models/regex_baseline.pkl',
        'HMM_Murni': 'models/hmm_pure.pkl',
        'CRF_Murni': 'models/crf_pure.pkl',
        'Hybrid_HMM': 'models/hybrid_hmm.pkl',
        'Hybrid_CRF': 'models/hybrid_crf.pkl',
    }
    
    # Compute false positive rate per category
    print("\n" + "="*70)
    print("  📊 FALSE POSITIVE RATE per CATEGORY")
    print("="*70)
    print("  (Lower is better for samples WITHOUT PII)")
    print()
    
    categories = df_tagged['category'].unique()
    
    print(f"  {'Model':<14}", end="")
    for cat in categories:
        print(f" {cat[:18]:<18}", end="")
    print()
    print("  " + "-"*100)
    
    results = {}
    
    for model_name, model_path in models_to_test.items():
        if not os.path.exists(model_path):
            continue
        
        # Load model
        if 'regex' in model_name.lower():
            regex_module = import_module('10_train_regex')
            model = regex_module.RegexModel.load(model_path)
            predict_fn = lambda tokens: model.predict_sequence(tokens)
        elif 'hmm' in model_name.lower() and 'hybrid' not in model_name.lower():
            hmm_module = import_module('11_train_hmm')
            model = hmm_module.CategoricalHMM.load(model_path)
            predict_fn = lambda tokens: model.viterbi_decode(tokens)
        elif 'hybrid_hmm' in model_name.lower():
            hybrid_hmm_module = import_module('13_train_hybrid_hmm')
            model = hybrid_hmm_module.HybridHMM.load(model_path)
            predict_fn = lambda tokens: model.viterbi_decode(tokens)
        elif 'hybrid_crf' in model_name.lower():
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            def predict_fn(tokens, m=model):
                feats = features_module.sentence_to_features(tokens, use_regex_features=True)
                return m.predict([feats])[0]
        elif 'crf' in model_name.lower():
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            def predict_fn(tokens, m=model):
                feats = features_module.sentence_to_features(tokens, use_regex_features=False)
                return m.predict([feats])[0]
        
        # Compute FP rate per category
        cat_results = {}
        for cat in categories:
            cat_df = df_tagged[df_tagged['category'] == cat]
            
            fp_count = 0
            fn_count = 0
            tp_count = 0
            
            for _, row in cat_df.iterrows():
                tokens = row['tokens']
                true_labels = row['labels']
                pred_labels = predict_fn(tokens)
                
                # For samples without PII (true all O):
                # Count any non-O prediction as FP
                if all(l == 'O' for l in true_labels):
                    if any(p != 'O' for p in pred_labels):
                        fp_count += 1
                # For samples with PII:
                # Check if NIK/PHONE detected correctly
                else:
                    has_correct = False
                    for t, true_l, pred_l in zip(tokens, true_labels, pred_labels):
                        if true_l.startswith('B-') and true_l == pred_l:
                            has_correct = True
                            break
                    if has_correct:
                        tp_count += 1
                    else:
                        fn_count += 1
            
            cat_results[cat] = {
                'fp': fp_count,
                'fn': fn_count,
                'tp': tp_count,
                'total': len(cat_df)
            }
        
        results[model_name] = cat_results
        
        # Print row
        print(f"  {model_name:<14}", end="")
        for cat in categories:
            r = cat_results[cat]
            if cat.startswith('context_free') or cat == 'near_pattern':
                # FP-focused (lower better)
                fp_rate = r['fp'] / r['total'] * 100
                marker = '❌' if fp_rate > 30 else ('⚠️ ' if fp_rate > 10 else '✅')
                print(f" {marker} FP:{fp_rate:>5.1f}%       ", end="")
            else:
                # TP-focused (higher better)
                tp_rate = r['tp'] / r['total'] * 100
                marker = '✅' if tp_rate > 80 else ('⚠️ ' if tp_rate > 50 else '❌')
                print(f" {marker} TP:{tp_rate:>5.1f}%       ", end="")
        print()
    
    # Summary
    print("\n" + "="*70)
    print("  🏆 ROBUSTNESS RANKING (Lower FP + Higher TP = Better)")
    print("="*70)
    
    rankings = []
    for model_name, cat_results in results.items():
        # Compute composite score
        total_fp = sum(r['fp'] for r in cat_results.values() 
                       if r.get('total', 0) > 0)
        total_tp = sum(r['tp'] for r in cat_results.values()
                       if r.get('total', 0) > 0)
        total_samples_with_pii = sum(r['total'] - r['fp'] for r in cat_results.values()
                                      if 'nik_unusual' in str(r) or 'nested' in str(r))
        
        # Simple score: TP rate - FP rate (range -100 to +100)
        score = total_tp - total_fp
        rankings.append((model_name, score, total_fp, total_tp))
    
    rankings.sort(key=lambda x: -x[1])
    
    for i, (name, score, fp, tp) in enumerate(rankings, 1):
        print(f"  {i}. {name:<15} Score: {score:+d}  (TP={tp}, FP={fp})")
    
    print("="*70)


if __name__ == "__main__":
    main()