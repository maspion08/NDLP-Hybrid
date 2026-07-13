"""
Compute Inter-Annotator Agreement (IAA) dari export JSON HumanSignal.

[VERSI TERBARU - Sesuai Pedoman Anotasi v3.0]
Menghitung TIGA metrik komplementer:
  1. Span-level Pairwise F1 (strict + relaxed)   -> METRIK UTAMA
  2. Cohen's Kappa (token-level, tanpa label "O") -> METRIK PELENGKAP
  3. Gwet's AC1 (token-level)                     -> METRIK PARADOX-RESISTANT

Input : ekspor JSON default dari HumanSignal (bukan JSON-MIN)
Output: laporan konsol + file JSON hasil (dipakai untuk Tabel Bab IV)

Cara pakai:
    python scripts/31_compute_inter_kappa.py \
        --input data/annotations/anotasi_raw_export.json \
        --output evaluation/iaa_result.json \
        --anotator-a argaavian1000@gmail.com \
        --anotator-b ghazali_email@example.com

Dependensi: pip install seqeval scikit-learn irrCAC pandas

Referensi:
- Hripcsak & Rothschild (2005). Agreement, the F-measure, and reliability in IR.
- Gwet (2008). Computing inter-rater reliability in the presence of high agreement.
- Tjong Kim Sang & De Meulder (2003). CoNLL-2003 shared task.
- Landis & Koch (1977). The measurement of observer agreement for categorical data.
"""
import os
import re
import sys
import json
import argparse
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional

import pandas as pd

# ═══════════════════════════════════════════════════════════════════════════
# TOKENIZER — konsisten dengan scripts/02_bio_tagger.py
# ═══════════════════════════════════════════════════════════════════════════

TOKEN_PATTERN = re.compile(r'\+62\d{8,12}|\d+|[a-zA-Z\u00C0-\u017F]+|[^\w\s]')


def tokenize_with_offsets(text: str) -> List[Tuple[str, int, int]]:
    """
    Tokenisasi teks yang MENGEMBALIKAN posisi karakter tiap token.
    
    Konsisten dengan tokenizer di 02_bio_tagger.py. Return list of
    (token, char_start, char_end) supaya kita bisa memetakan span
    dari HumanSignal (yang pakai char offset) ke token index.
    """
    tokens = []
    for m in TOKEN_PATTERN.finditer(text):
        tokens.append((m.group(), m.start(), m.end()))
    return tokens


# ═══════════════════════════════════════════════════════════════════════════
# KONVERSI: span HumanSignal (char offset) -> label BIO per token
# ═══════════════════════════════════════════════════════════════════════════

def spans_to_bio(text: str, spans: List[Dict]) -> Tuple[List[str], List[str]]:
    """
    Konversi list span (dari HumanSignal result[i].value) menjadi
    (list_token, list_label_BIO).
    
    span: dict dengan key 'start', 'end', 'labels' (label entitas)
    """
    tokens_with_offsets = tokenize_with_offsets(text)
    tokens = [t[0] for t in tokens_with_offsets]
    labels = ["O"] * len(tokens)
    
    # Urutkan span berdasarkan start untuk hindari tumpang tindih tak menentu
    spans_sorted = sorted(spans, key=lambda s: s.get('start', 0))
    
    for span in spans_sorted:
        s_start = span.get('start')
        s_end = span.get('end')
        s_labels = span.get('labels', [])
        if not s_labels or s_start is None or s_end is None:
            continue
        entity_type = s_labels[0]  # ambil label pertama
        
        # Cari token yang overlap dengan rentang [s_start, s_end)
        matched_token_idxs = []
        for i, (_, t_start, t_end) in enumerate(tokens_with_offsets):
            # Token dianggap masuk span kalau ada overlap
            if t_end > s_start and t_start < s_end:
                matched_token_idxs.append(i)
        
        if not matched_token_idxs:
            continue
        
        # Set BIO: token pertama = B-, sisanya = I-
        for j, idx in enumerate(matched_token_idxs):
            prefix = "B-" if j == 0 else "I-"
            labels[idx] = f"{prefix}{entity_type}"
    
    return tokens, labels


# ═══════════════════════════════════════════════════════════════════════════
# LOADER: parse ekspor HumanSignal -> struktur (task_id, anotator, tokens, labels)
# ═══════════════════════════════════════════════════════════════════════════

def load_humansignal_export(
    filepath: str,
    anotator_a_id: str,
    anotator_b_id: str,
) -> pd.DataFrame:
    """
    Baca file JSON ekspor HumanSignal, kembalikan DataFrame dengan kolom:
      task_id, inner_id, text, meta_format, anotator, tokens, labels
    
    anotator_a_id / anotator_b_id: email atau numeric user id
    Fungsi ini otomatis mendeteksi apakah anotator diberi sebagai email atau id.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"[INFO] Total task di file: {len(data)}")
    
    rows = []
    tasks_with_zero = 0
    tasks_with_one = 0
    tasks_with_two_or_more = 0
    
    for task in data:
        anns = task.get('annotations', [])
        if len(anns) == 0:
            tasks_with_zero += 1
            continue
        elif len(anns) == 1:
            tasks_with_one += 1
        else:
            tasks_with_two_or_more += 1
        
        text = task.get('data', {}).get('text', '')
        meta_format = task.get('data', {}).get('meta_format', 'unknown')
        
        for ann in anns:
            completed_by = ann.get('completed_by', {})
            if isinstance(completed_by, dict):
                email = completed_by.get('email', '')
                uid = str(completed_by.get('id', ''))
            else:
                email = ''
                uid = str(completed_by)
            
            # Cocokkan dengan salah satu anotator
            if anotator_a_id in (email, uid):
                anotator_role = 'A'
            elif anotator_b_id in (email, uid):
                anotator_role = 'B'
            else:
                # bukan A maupun B (misal ada anotator lain di proyek); skip
                continue
            
            spans = []
            for r in ann.get('result', []):
                if r.get('type') == 'labels':
                    spans.append(r.get('value', {}))
            
            tokens, labels = spans_to_bio(text, spans)
            rows.append({
                'task_id': task['id'],
                'inner_id': task.get('inner_id'),
                'text': text,
                'meta_format': meta_format,
                'anotator': anotator_role,
                'tokens': tokens,
                'labels': labels,
            })
    
    print(f"[INFO] Task tanpa anotasi          : {tasks_with_zero}")
    print(f"[INFO] Task dengan 1 anotasi       : {tasks_with_one}")
    print(f"[INFO] Task dengan 2+ anotasi      : {tasks_with_two_or_more}")
    
    df = pd.DataFrame(rows)
    print(f"[INFO] Total baris (task x anotator): {len(df)}")
    
    return df


# ═══════════════════════════════════════════════════════════════════════════
# 1. SPAN-LEVEL PAIRWISE F1 (Strict & Relaxed)
# ═══════════════════════════════════════════════════════════════════════════

def bio_to_spans(labels: List[str]) -> List[Tuple[int, int, str]]:
    """
    Konversi BIO tag sequence -> list of (start_idx, end_idx, entity_type)
    (indeks token, end inclusive)
    """
    spans = []
    i = 0
    n = len(labels)
    while i < n:
        lab = labels[i]
        if lab.startswith('B-'):
            ent_type = lab[2:]
            start = i
            end = i
            j = i + 1
            while j < n and labels[j] == f'I-{ent_type}':
                end = j
                j += 1
            spans.append((start, end, ent_type))
            i = j
        else:
            i += 1
    return spans


def compute_span_f1(
    labels_a: List[List[str]],
    labels_b: List[List[str]],
    mode: str = 'strict',
) -> Dict[str, Dict[str, float]]:
    """
    Hitung Span-level Pairwise F1 antara Anotator A dan B.
    
    mode = 'strict'  -> match perlu (start, end, type) identik
    mode = 'relaxed' -> match cukup (type sama) dan overlap >= 1 token
    
    Return dict {entity: {'precision': ..., 'recall': ..., 'f1': ..., 'tp':..., 'fp':..., 'fn':...}}
    plus '_macro' dan '_micro'.
    """
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)
    
    for lab_a, lab_b in zip(labels_a, labels_b):
        spans_a = bio_to_spans(lab_a)
        spans_b = bio_to_spans(lab_b)
        
        if mode == 'strict':
            set_a = set(spans_a)
            set_b = set(spans_b)
            common = set_a & set_b
            for _, _, t in common:
                tp[t] += 1
            for _, _, t in (set_a - common):
                fn[t] += 1  # A punya, B tidak -> A dianggap gold, B "miss"
            for _, _, t in (set_b - common):
                fp[t] += 1  # B claim, A tidak
        
        else:  # relaxed
            matched_a = set()
            matched_b = set()
            for i, (sa, ea, ta) in enumerate(spans_a):
                for j, (sb, eb, tb) in enumerate(spans_b):
                    if ta != tb:
                        continue
                    # Overlap?
                    if not (ea < sb or eb < sa):
                        matched_a.add(i)
                        matched_b.add(j)
                        tp[ta] += 1
                        break
            for i, (_, _, t) in enumerate(spans_a):
                if i not in matched_a:
                    fn[t] += 1
            for j, (_, _, t) in enumerate(spans_b):
                if j not in matched_b:
                    fp[t] += 1
    
    entities = sorted(set(list(tp.keys()) + list(fp.keys()) + list(fn.keys())))
    result = {}
    p_sum, r_sum, f_sum = 0, 0, 0
    tp_total, fp_total, fn_total = 0, 0, 0
    
    for ent in entities:
        t, f_, n_ = tp[ent], fp[ent], fn[ent]
        prec = t / (t + f_) if (t + f_) else 0.0
        rec = t / (t + n_) if (t + n_) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        result[ent] = {
            'precision': round(prec, 4),
            'recall': round(rec, 4),
            'f1': round(f1, 4),
            'tp': t, 'fp': f_, 'fn': n_,
        }
        p_sum += prec; r_sum += rec; f_sum += f1
        tp_total += t; fp_total += f_; fn_total += n_
    
    k = len(entities) if entities else 1
    result['_macro'] = {
        'precision': round(p_sum / k, 4),
        'recall': round(r_sum / k, 4),
        'f1': round(f_sum / k, 4),
    }
    p_mi = tp_total / (tp_total + fp_total) if (tp_total + fp_total) else 0.0
    r_mi = tp_total / (tp_total + fn_total) if (tp_total + fn_total) else 0.0
    f_mi = 2 * p_mi * r_mi / (p_mi + r_mi) if (p_mi + r_mi) else 0.0
    result['_micro'] = {
        'precision': round(p_mi, 4),
        'recall': round(r_mi, 4),
        'f1': round(f_mi, 4),
    }
    return result


# ═══════════════════════════════════════════════════════════════════════════
# 2. COHEN'S KAPPA (token-level, tanpa "O")
# ═══════════════════════════════════════════════════════════════════════════

def compute_cohens_kappa_no_o(
    labels_a: List[List[str]],
    labels_b: List[List[str]],
) -> Dict[str, float]:
    """
    Hitung Cohen's Kappa hanya pada subset token yang di-tag entity
    oleh setidaknya salah satu anotator (menghindari kappa paradox dari
    kelas mayoritas "O").
    """
    from sklearn.metrics import cohen_kappa_score
    
    flat_a, flat_b = [], []
    for lab_a, lab_b in zip(labels_a, labels_b):
        for a, b in zip(lab_a, lab_b):
            if a != "O" or b != "O":
                flat_a.append(a)
                flat_b.append(b)
    
    if len(flat_a) < 2:
        return {'macro_kappa': 0.0, 'agreement': 0.0, 'n_tokens_considered': 0}
    
    k = cohen_kappa_score(flat_a, flat_b)
    # Raw agreement
    agree = sum(1 for a, b in zip(flat_a, flat_b) if a == b) / len(flat_a)
    
    return {
        'macro_kappa': round(k, 4),
        'agreement': round(agree, 4),
        'n_tokens_considered': len(flat_a),
        'interpretation': interpret_landis_koch(k),
    }


def compute_kappa_per_entity(
    labels_a: List[List[str]],
    labels_b: List[List[str]],
    entities: List[str],
) -> Dict[str, Dict[str, float]]:
    """Cohen's Kappa binary per entitas (in-entity vs not-in-entity)."""
    from sklearn.metrics import cohen_kappa_score
    
    result = {}
    for ent in entities:
        flat_a, flat_b = [], []
        for lab_a, lab_b in zip(labels_a, labels_b):
            for a, b in zip(lab_a, lab_b):
                # Perlakukan sebagai binary: token ini bertag entitas ini (B-/I-) atau bukan
                is_a = a.endswith(f'-{ent}')
                is_b = b.endswith(f'-{ent}')
                flat_a.append(int(is_a))
                flat_b.append(int(is_b))
        
        if len(set(flat_a)) < 2 or len(set(flat_b)) < 2:
            # Hanya 1 kelas -> Kappa tidak terdefinisi
            k = 1.0 if flat_a == flat_b else 0.0
        else:
            k = cohen_kappa_score(flat_a, flat_b)
        
        result[ent] = {
            'kappa': round(k, 4),
            'interpretation': interpret_landis_koch(k),
        }
    return result


# ═══════════════════════════════════════════════════════════════════════════
# 3. GWET'S AC1 (token-level)
# ═══════════════════════════════════════════════════════════════════════════

def compute_gwet_ac1(
    labels_a: List[List[str]],
    labels_b: List[List[str]],
    per_entity: bool = False,
    entities: Optional[List[str]] = None,
) -> Dict[str, float]:
    """
    Hitung Gwet's AC1 pada seluruh token (termasuk O).
    Menggunakan library irrCAC yang mengimplementasikan Gwet (2008).
    
    Kalau per_entity=True, hitung juga AC1 binary per entitas.
    """
    try:
        from irrCAC.raw import CAC
    except ImportError:
        return {
            'error': 'irrCAC belum terpasang. Install dengan: pip install irrCAC'
        }
    
    result = {}
    
    # === Overall (semua label termasuk O) ===
    all_a, all_b = [], []
    for lab_a, lab_b in zip(labels_a, labels_b):
        all_a.extend(lab_a)
        all_b.extend(lab_b)
    
    if len(all_a) < 2:
        result['macro_ac1'] = 0.0
    else:
        df = pd.DataFrame({'A': all_a, 'B': all_b})
        cac = CAC(df)
        gwet = cac.gwet()
        est = gwet['est']
        result['macro_ac1'] = round(est['coefficient_value'], 4)
        result['ac1_ci'] = est['confidence_interval']
        result['interpretation'] = interpret_landis_koch(est['coefficient_value'])
        result['n_tokens_considered'] = len(all_a)
    
    # === Per entitas (binary) ===
    if per_entity and entities:
        per_ent = {}
        for ent in entities:
            bin_a, bin_b = [], []
            for lab_a, lab_b in zip(labels_a, labels_b):
                for a, b in zip(lab_a, lab_b):
                    bin_a.append('YES' if a.endswith(f'-{ent}') else 'NO')
                    bin_b.append('YES' if b.endswith(f'-{ent}') else 'NO')
            if len(set(bin_a)) < 2 and bin_a == bin_b:
                per_ent[ent] = {'ac1': 1.0, 'interpretation': interpret_landis_koch(1.0)}
                continue
            df = pd.DataFrame({'A': bin_a, 'B': bin_b})
            try:
                gwet = CAC(df).gwet()
                val = gwet['est']['coefficient_value']
                per_ent[ent] = {
                    'ac1': round(val, 4),
                    'interpretation': interpret_landis_koch(val),
                }
            except Exception as e:
                per_ent[ent] = {'ac1': None, 'error': str(e)}
        result['per_entity'] = per_ent
    
    return result


# ═══════════════════════════════════════════════════════════════════════════
# HELPER: interpretasi Landis & Koch
# ═══════════════════════════════════════════════════════════════════════════

def interpret_landis_koch(value: float) -> str:
    if value < 0:
        return "Poor"
    elif value < 0.20:
        return "Slight"
    elif value < 0.40:
        return "Fair"
    elif value < 0.60:
        return "Moderate"
    elif value < 0.80:
        return "Substantial"
    else:
        return "Almost Perfect"


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def build_pairs(df: pd.DataFrame) -> Tuple[List[List[str]], List[List[str]], pd.DataFrame]:
    """
    Ambil pasangan (A, B) untuk task yang dianotasi KEDUA anotator.
    Return: labels_a, labels_b, dan DataFrame task yang overlap.
    """
    # Pivot: task_id x anotator -> list label
    if df.empty:
        return [], [], pd.DataFrame()
    
    pivot = df.pivot_table(
        index='task_id',
        columns='anotator',
        values='labels',
        aggfunc='first'
    )
    # Cek kedua anotator ada
    if 'A' not in pivot.columns or 'B' not in pivot.columns:
        missing = [x for x in ('A', 'B') if x not in pivot.columns]
        print(f"\n[WARN] Kolom anotator berikut TIDAK ADA di data: {missing}")
        print("       Kemungkinan penyebab:")
        if 'A' in missing:
            print("       - Email/ID Anotator A salah (cek --anotator-a)")
        if 'B' in missing:
            print("       - Anotator B belum submit anotasi manapun, atau")
            print("       - Email/ID Anotator B salah (cek --anotator-b)")
        return [], [], pd.DataFrame()
    
    # Hanya task yang punya A dan B
    overlap = pivot.dropna(subset=['A', 'B'])
    
    labels_a = overlap['A'].tolist()
    labels_b = overlap['B'].tolist()
    
    # Verifikasi panjang token sama
    task_meta = df.drop_duplicates('task_id')[['task_id', 'inner_id', 'meta_format']].set_index('task_id')
    overlap_meta = task_meta.loc[overlap.index]
    
    return labels_a, labels_b, overlap_meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True,
                        help='Path ke ekspor JSON HumanSignal')
    parser.add_argument('--output', default='evaluation/iaa_result.json',
                        help='Path keluaran JSON hasil')
    parser.add_argument('--anotator-a', required=True,
                        help='Email atau user ID Anotator A (peneliti)')
    parser.add_argument('--anotator-b', required=True,
                        help='Email atau user ID Anotator B (independen)')
    args = parser.parse_args()
    
    entities = ['NIK', 'PHONE', 'NAMA', 'JABATAN', 'LOKASI']
    
    print("=" * 78)
    print("  INTER-ANNOTATOR AGREEMENT COMPUTATION")
    print("  Sesuai Pedoman Anotasi v3.0 - TA Arga Ariyuda Avian")
    print("=" * 78)
    print(f"\n[INFO] Input file      : {args.input}")
    print(f"[INFO] Anotator A      : {args.anotator_a}")
    print(f"[INFO] Anotator B      : {args.anotator_b}")
    print(f"[INFO] Entitas         : {entities}\n")
    
    df = load_humansignal_export(args.input, args.anotator_a, args.anotator_b)
    labels_a, labels_b, overlap_meta = build_pairs(df)
    
    n_pairs = len(labels_a)
    print(f"\n[INFO] Pasangan task overlap (A & B): {n_pairs}\n")
    
    if n_pairs == 0:
        print("[ERROR] Tidak ada task yang dianotasi oleh KEDUA anotator.")
        print("        Periksa:")
        print("        1. Setting HumanSignal: Overlap of Annotations = 100%")
        print("        2. Anotator B sudah tersubmit anotasi")
        print("        3. Email/ID Anotator B benar (cek dengan --anotator-b)")
        sys.exit(1)
    
    # ─────────────────────────────────────
    # 1. Span-level Pairwise F1
    # ─────────────────────────────────────
    print("=" * 78)
    print("  METRIK 1/3: SPAN-LEVEL PAIRWISE F1")
    print("=" * 78)
    
    print("\n[STRICT]")
    span_strict = compute_span_f1(labels_a, labels_b, mode='strict')
    print(f"{'Entitas':<10}{'Prec':>10}{'Rec':>10}{'F1':>10}{'TP':>6}{'FP':>6}{'FN':>6}")
    print("-" * 60)
    for ent in entities:
        if ent in span_strict:
            m = span_strict[ent]
            print(f"{ent:<10}{m['precision']:>10.4f}{m['recall']:>10.4f}{m['f1']:>10.4f}"
                  f"{m['tp']:>6}{m['fp']:>6}{m['fn']:>6}")
    print("-" * 60)
    m = span_strict['_macro']
    print(f"{'Macro':<10}{m['precision']:>10.4f}{m['recall']:>10.4f}{m['f1']:>10.4f}")
    m = span_strict['_micro']
    print(f"{'Micro':<10}{m['precision']:>10.4f}{m['recall']:>10.4f}{m['f1']:>10.4f}")
    
    print("\n[RELAXED]")
    span_relaxed = compute_span_f1(labels_a, labels_b, mode='relaxed')
    print(f"{'Entitas':<10}{'Prec':>10}{'Rec':>10}{'F1':>10}")
    print("-" * 42)
    for ent in entities:
        if ent in span_relaxed:
            m = span_relaxed[ent]
            print(f"{ent:<10}{m['precision']:>10.4f}{m['recall']:>10.4f}{m['f1']:>10.4f}")
    print("-" * 42)
    m = span_relaxed['_macro']
    print(f"{'Macro':<10}{m['precision']:>10.4f}{m['recall']:>10.4f}{m['f1']:>10.4f}")
    
    # Selisih strict vs relaxed
    diff = span_relaxed['_macro']['f1'] - span_strict['_macro']['f1']
    print(f"\nSelisih (Relaxed - Strict) Macro F1: {diff:+.4f}")
    print("  -> Selisih besar mengindikasikan boundary error adalah sumber utama ketidaksepakatan.")
    
    # ─────────────────────────────────────
    # 2. Cohen's Kappa (tanpa O)
    # ─────────────────────────────────────
    print("\n" + "=" * 78)
    print("  METRIK 2/3: COHEN'S KAPPA (token-level, tanpa \"O\")")
    print("=" * 78)
    
    cohen = compute_cohens_kappa_no_o(labels_a, labels_b)
    print(f"\nMacro Kappa               : {cohen['macro_kappa']:.4f} ({cohen['interpretation']})")
    print(f"Raw Agreement (tanpa O)   : {cohen['agreement']:.4f}")
    print(f"Token dipertimbangkan     : {cohen['n_tokens_considered']}")
    
    print("\n[Per Entitas - Binary Kappa]")
    kappa_per = compute_kappa_per_entity(labels_a, labels_b, entities)
    print(f"{'Entitas':<10}{'Kappa':>10}  {'Kategori':<20}")
    print("-" * 44)
    for ent in entities:
        m = kappa_per[ent]
        print(f"{ent:<10}{m['kappa']:>10.4f}  {m['interpretation']:<20}")
    
    # ─────────────────────────────────────
    # 3. Gwet's AC1
    # ─────────────────────────────────────
    print("\n" + "=" * 78)
    print("  METRIK 3/3: GWET's AC1 (token-level, paradox-resistant)")
    print("=" * 78)
    
    gwet = compute_gwet_ac1(labels_a, labels_b, per_entity=True, entities=entities)
    if 'error' in gwet:
        print(f"\n[SKIP] {gwet['error']}")
    else:
        print(f"\nMacro AC1                 : {gwet['macro_ac1']:.4f} ({gwet['interpretation']})")
        if 'ac1_ci' in gwet:
            print(f"95% Confidence Interval   : {gwet['ac1_ci']}")
        print(f"Token dipertimbangkan     : {gwet['n_tokens_considered']}")
        
        if 'per_entity' in gwet:
            print("\n[Per Entitas - Binary AC1]")
            print(f"{'Entitas':<10}{'AC1':>10}  {'Kategori':<20}")
            print("-" * 44)
            for ent in entities:
                m = gwet['per_entity'].get(ent, {})
                if 'ac1' in m and m['ac1'] is not None:
                    print(f"{ent:<10}{m['ac1']:>10.4f}  {m['interpretation']:<20}")
                else:
                    print(f"{ent:<10}     (error)  {m.get('error', '-')}")
    
    # ─────────────────────────────────────
    # EVALUASI TARGET
    # ─────────────────────────────────────
    print("\n" + "=" * 78)
    print("  EVALUASI TARGET (Pedoman v3.0 Bagian I.5)")
    print("=" * 78)
    
    target_span_f1 = 0.75
    target_ac1 = 0.80
    
    actual_span_f1 = span_strict['_macro']['f1']
    actual_ac1 = gwet.get('macro_ac1', 0)
    
    status_span = "TERCAPAI" if actual_span_f1 >= target_span_f1 else "TIDAK TERCAPAI"
    status_ac1 = "TERCAPAI" if actual_ac1 >= target_ac1 else "TIDAK TERCAPAI"
    
    print(f"\n  Target 1: Span-F1 strict Macro >= {target_span_f1}")
    print(f"           Aktual: {actual_span_f1:.4f}  -> {status_span}")
    print(f"\n  Target 2: Gwet's AC1 Macro >= {target_ac1}")
    print(f"           Aktual: {actual_ac1:.4f}  -> {status_ac1}")
    
    all_ok = (status_span == "TERCAPAI" and status_ac1 == "TERCAPAI")
    
    print("\n" + "=" * 78)
    if all_ok:
        print("  KESIMPULAN: Kedua target IAA TERCAPAI.")
        print("              Anotasi dapat langsung digunakan sebagai ground truth.")
    else:
        print("  KESIMPULAN: Salah satu atau kedua target TIDAK tercapai.")
        print("              Lakukan tahap ADJUDIKASI sesuai Pedoman Bagian I.6.")
    print("=" * 78)
    
    # ─────────────────────────────────────
    # Simpan output
    # ─────────────────────────────────────
    output_data = {
        'meta': {
            'n_pairs': n_pairs,
            'anotator_a': args.anotator_a,
            'anotator_b': args.anotator_b,
            'entities': entities,
        },
        'span_f1_strict': span_strict,
        'span_f1_relaxed': span_relaxed,
        'cohen_kappa': {
            'overall': cohen,
            'per_entity': kappa_per,
        },
        'gwet_ac1': gwet,
        'target_evaluation': {
            'target_span_f1': target_span_f1,
            'actual_span_f1': actual_span_f1,
            'status_span_f1': status_span,
            'target_ac1': target_ac1,
            'actual_ac1': actual_ac1,
            'status_ac1': status_ac1,
            'all_targets_met': all_ok,
        },
    }
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n[INFO] Hasil lengkap disimpan ke: {args.output}")


if __name__ == '__main__':
    main()