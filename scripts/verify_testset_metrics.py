"""
Evaluate All 5 Models on TEST SET (in-distribution / synthetic).

Skrip ini adalah mirror dari 21_evaluate_holdout.py, tetapi menggunakan
data/processed/test.pkl sebagai input, bukan naturalistic_bio.pkl.

Tujuan: memverifikasi angka F1 per entitas dan Macro F1 pada Test Set
yang tercantum di Tabel 4.15 skripsi, khususnya untuk baris Hybrid HMM
yang saat ini masih inkonsisten.

Cara pakai:
    python scripts/verify_testset_metrics.py

Output:
    - Print report per model (5 model)
    - Simpan ke evaluation/testset_verification.json
"""
import os
import sys
import json
import time
import pickle
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
features_module = import_module('07_features')
evaluator = import_module('08_evaluator')


def load_testset():
    """Load Test Set (dari data/processed/test.pkl)"""
    path = 'data/processed/test.pkl'
    if not os.path.exists(path):
        print(f"[ERROR] Test set not found: {path}")
        print("   Jalankan scripts/03_split_dataset.py terlebih dahulu.")
        return None
    return pd.read_pickle(path)


def evaluate_regex(df):
    print("\n" + "="*70)
    print("  EVALUATING: Regex Murni (Test Set)")
    print("="*70)
    if not os.path.exists('models/regex_baseline.pkl'):
        print("[SKIP] models/regex_baseline.pkl not found")
        return None
    regex_module = import_module('10_train_regex')
    model = regex_module.RegexModel.load('models/regex_baseline.pkl')
    X_tokens = df['tokens'].tolist()
    y_true = df['labels'].tolist()
    start = time.perf_counter()
    y_pred = model.predict(X_tokens)
    elapsed = time.perf_counter() - start
    metrics = evaluator.compute_entity_metrics(y_true, y_pred, X_tokens)
    metrics['_inference_time_s'] = elapsed
    evaluator.print_classification_report(metrics, model_name="Regex_Murni")
    return metrics


def evaluate_hmm(df):
    print("\n" + "="*70)
    print("  EVALUATING: HMM Murni (Test Set)")
    print("="*70)
    if not os.path.exists('models/hmm.pkl'):
        print("[SKIP] models/hmm.pkl not found")
        return None
    hmm_module = import_module('11_train_hmm')
    model = hmm_module.HMMModel.load('models/hmm.pkl')
    X_tokens = df['tokens'].tolist()
    y_true = df['labels'].tolist()
    start = time.perf_counter()
    y_pred = model.predict(X_tokens)
    elapsed = time.perf_counter() - start
    metrics = evaluator.compute_entity_metrics(y_true, y_pred, X_tokens)
    metrics['_inference_time_s'] = elapsed
    evaluator.print_classification_report(metrics, model_name="HMM_Murni")
    return metrics


def evaluate_crf(df):
    print("\n" + "="*70)
    print("  EVALUATING: CRF Murni (Test Set)")
    print("="*70)
    if not os.path.exists('models/crf_pure.pkl'):
        print("[SKIP] models/crf_pure.pkl not found")
        return None
    with open('models/crf_pure.pkl', 'rb') as f:
        model = pickle.load(f)
    X_feats, y_true = features_module.dataset_to_features(
        df, use_regex_features=False, verbose=False
    )
    X_tokens = df['tokens'].tolist()
    start = time.perf_counter()
    y_pred = model.predict(X_feats)
    elapsed = time.perf_counter() - start
    metrics = evaluator.compute_entity_metrics(y_true, y_pred, X_tokens)
    metrics['_inference_time_s'] = elapsed
    evaluator.print_classification_report(metrics, model_name="CRF_Murni")
    return metrics


def evaluate_hybrid_hmm(df):
    print("\n" + "="*70)
    print("  EVALUATING: Hybrid HMM (Test Set)")
    print("="*70)
    if not os.path.exists('models/hybrid_hmm.pkl'):
        print("[SKIP] models/hybrid_hmm.pkl not found")
        return None
    hmm_module = import_module('13_train_hybrid_hmm')
    model = hmm_module.HybridHMM.load('models/hybrid_hmm.pkl')
    X_tokens = df['tokens'].tolist()
    y_true = df['labels'].tolist()
    start = time.perf_counter()
    y_pred = model.predict(X_tokens)
    elapsed = time.perf_counter() - start
    metrics = evaluator.compute_entity_metrics(y_true, y_pred, X_tokens)
    metrics['_inference_time_s'] = elapsed
    evaluator.print_classification_report(metrics, model_name="Hybrid_HMM")
    return metrics


def evaluate_hybrid_crf(df):
    print("\n" + "="*70)
    print("  EVALUATING: Hybrid CRF (Test Set)")
    print("="*70)
    if not os.path.exists('models/hybrid_crf.pkl'):
        print("[SKIP] models/hybrid_crf.pkl not found")
        return None
    with open('models/hybrid_crf.pkl', 'rb') as f:
        model = pickle.load(f)
    X_feats, y_true = features_module.dataset_to_features(
        df, use_regex_features=True, verbose=False
    )
    X_tokens = df['tokens'].tolist()
    start = time.perf_counter()
    y_pred = model.predict(X_feats)
    elapsed = time.perf_counter() - start
    metrics = evaluator.compute_entity_metrics(y_true, y_pred, X_tokens)
    metrics['_inference_time_s'] = elapsed
    evaluator.print_classification_report(metrics, model_name="Hybrid_CRF")
    return metrics


def main():
    print("="*70)
    print("  TEST SET VERIFICATION - All 5 Models")
    print("  Tugas Akhir: Arga Ariyuda Avian (2221101774)")
    print("  Tujuan: verifikasi angka Tabel 4.15 di skripsi")
    print("="*70)

    df_test = load_testset()
    if df_test is None:
        return
    print(f"\n[OK] Test set loaded: {len(df_test)} samples")

    results = {
        'Regex_Murni': evaluate_regex(df_test),
        'HMM_Murni': evaluate_hmm(df_test),
        'CRF_Murni': evaluate_crf(df_test),
        'Hybrid_HMM': evaluate_hybrid_hmm(df_test),
        'Hybrid_CRF': evaluate_hybrid_crf(df_test),
    }

    # ─────────────────────────────────────
    # Ringkasan tabel per-entitas (persis format Tabel 4.15)
    # ─────────────────────────────────────
    print("\n" + "="*80)
    print("  RINGKASAN: F1-Score per Entitas pada TEST SET (Tabel 4.15)")
    print("="*80)

    entities = ['NIK', 'PHONE', 'NAMA', 'JABATAN', 'LOKASI']
    header = f"  {'Model':<15}" + "".join(f"{e:>10}" for e in entities) + f"{'Macro F1':>12}"
    print("\n" + header)
    print("  " + "-" * (15 + 10*5 + 12))

    summary_table = {}
    for name, m in results.items():
        if m is None:
            print(f"  {name:<15}  (tidak tersedia)")
            continue
        row = f"  {name:<15}"
        row_data = {}
        for ent in entities:
            f1 = m.get(ent, {}).get('f1', 0.0)
            row += f"{f1:>10.4f}"
            row_data[ent] = round(f1, 4)
        macro_f1 = m['_macro']['f1']
        row += f"{macro_f1:>12.4f}"
        row_data['Macro_F1'] = round(macro_f1, 4)
        summary_table[name] = row_data
        print(row)

    # ─────────────────────────────────────
    # Cek konsistensi: apakah Macro F1 = rata-rata per-entitas?
    # ─────────────────────────────────────
    print("\n" + "="*80)
    print("  VERIFIKASI: Apakah Macro F1 = rata-rata 5 angka per-entitas?")
    print("="*80)
    for name, m in results.items():
        if m is None:
            continue
        per_ent = [m[e]['f1'] for e in entities]
        avg = sum(per_ent) / 5
        macro = m['_macro']['f1']
        status = "OK" if abs(avg - macro) < 1e-4 else "MISMATCH!"
        print(f"  {name:<15}  rata2 per-ent = {avg:.4f}  |  Macro F1 = {macro:.4f}  [{status}]")

    # Save
    out_path = 'evaluation/testset_verification.json'
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    def _clean(d):
        if isinstance(d, dict):
            return {k: _clean(v) for k, v in d.items()}
        if isinstance(d, (list, tuple)):
            return [_clean(x) for x in d]
        if hasattr(d, 'item'):
            return d.item()
        return d

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'summary_table': summary_table,
            'per_model_full': _clean(results),
        }, f, indent=2)
    print(f"\n[OK] Hasil disimpan ke: {out_path}")


if __name__ == '__main__':
    main()
