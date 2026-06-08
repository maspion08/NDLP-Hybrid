"""
Evaluation Helper untuk Model Komparasi
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Menyediakan metrik standar:
- Precision, Recall, F1-Score per entity (B-only)
- Macro F1-Score (rata-rata across entities)
- Confusion matrix
- Classification report
"""
import json
import os
from collections import defaultdict


def extract_entities(tokens, labels):
    """
    Extract entities dari sequence labeling result.
    Group consecutive B-X dan I-X jadi 1 entity.
    
    Returns:
        list of (entity_type, entity_value, start_idx, end_idx)
    """
    entities = []
    current_type = None
    current_tokens = []
    current_start = None
    
    for i, (token, label) in enumerate(zip(tokens, labels)):
        if label.startswith('B-'):
            # Save previous entity
            if current_type:
                entities.append((
                    current_type,
                    ' '.join(current_tokens),
                    current_start,
                    i - 1
                ))
            # Start new entity
            current_type = label[2:]
            current_tokens = [token]
            current_start = i
        elif label.startswith('I-') and current_type == label[2:]:
            current_tokens.append(token)
        else:
            # Save and reset
            if current_type:
                entities.append((
                    current_type,
                    ' '.join(current_tokens),
                    current_start,
                    i - 1
                ))
            current_type = None
            current_tokens = []
            current_start = None
    
    # Save last entity
    if current_type:
        entities.append((
            current_type,
            ' '.join(current_tokens),
            current_start,
            len(tokens) - 1
        ))
    
    return entities


def compute_entity_metrics(y_true_seqs, y_pred_seqs, tokens_seqs):
    """
    Compute Precision, Recall, F1 per entity type.
    Menggunakan exact match (entity dianggap benar jika type DAN span match).
    
    Args:
        y_true_seqs: list of lists (true labels)
        y_pred_seqs: list of lists (predicted labels)
        tokens_seqs: list of lists (tokens)
    
    Returns:
        dict dengan metrics per entity dan macro
    """
    # TP, FP, FN per entity type
    counts = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0})
    
    for tokens, y_true, y_pred in zip(tokens_seqs, y_true_seqs, y_pred_seqs):
        true_entities = set(extract_entities(tokens, y_true))
        pred_entities = set(extract_entities(tokens, y_pred))
        
        # True Positives: yang ada di true DAN pred
        tp = true_entities & pred_entities
        # False Positives: yang di pred tapi tidak di true
        fp = pred_entities - true_entities
        # False Negatives: yang di true tapi tidak di pred
        fn = true_entities - pred_entities
        
        for ent in tp:
            counts[ent[0]]['tp'] += 1
        for ent in fp:
            counts[ent[0]]['fp'] += 1
        for ent in fn:
            counts[ent[0]]['fn'] += 1
    
    # Compute metrics
    metrics = {}
    entity_types = sorted(counts.keys())
    
    for ent_type in entity_types:
        tp = counts[ent_type]['tp']
        fp = counts[ent_type]['fp']
        fn = counts[ent_type]['fn']
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        support = tp + fn  # Total true entities
        
        metrics[ent_type] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': support,
            'tp': tp,
            'fp': fp,
            'fn': fn
        }
    
    # Macro averages
    if entity_types:
        macro_precision = sum(metrics[e]['precision'] for e in entity_types) / len(entity_types)
        macro_recall = sum(metrics[e]['recall'] for e in entity_types) / len(entity_types)
        macro_f1 = sum(metrics[e]['f1'] for e in entity_types) / len(entity_types)
        
        # Micro averages (weighted by support)
        total_tp = sum(metrics[e]['tp'] for e in entity_types)
        total_fp = sum(metrics[e]['fp'] for e in entity_types)
        total_fn = sum(metrics[e]['fn'] for e in entity_types)
        
        micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        micro_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
        micro_f1 = (2 * micro_precision * micro_recall / (micro_precision + micro_recall)) if (micro_precision + micro_recall) > 0 else 0.0
    else:
        macro_precision = macro_recall = macro_f1 = 0.0
        micro_precision = micro_recall = micro_f1 = 0.0
    
    metrics['_macro'] = {
        'precision': macro_precision,
        'recall': macro_recall,
        'f1': macro_f1
    }
    metrics['_micro'] = {
        'precision': micro_precision,
        'recall': micro_recall,
        'f1': micro_f1
    }
    
    return metrics


def print_classification_report(metrics, model_name="Model"):
    """Print classification report yang nice formatted"""
    print("\n" + "="*70)
    print(f"  📊 CLASSIFICATION REPORT - {model_name}")
    print("="*70)
    print(f"\n  {'Entity':<12} {'Precision':>10} {'Recall':>10} {'F1-Score':>10} {'Support':>10}")
    print("  " + "-"*64)
    
    entity_types = sorted([k for k in metrics.keys() if not k.startswith('_')])
    
    for ent in entity_types:
        m = metrics[ent]
        print(f"  {ent:<12} {m['precision']:>10.4f} {m['recall']:>10.4f} {m['f1']:>10.4f} {m['support']:>10}")
    
    print("  " + "-"*64)
    
    macro = metrics['_macro']
    micro = metrics['_micro']
    print(f"  {'Macro Avg':<12} {macro['precision']:>10.4f} {macro['recall']:>10.4f} {macro['f1']:>10.4f}")
    print(f"  {'Micro Avg':<12} {micro['precision']:>10.4f} {micro['recall']:>10.4f} {micro['f1']:>10.4f}")
    print("="*70)
    
    # Verdict
    target = 0.80
    print(f"\n  🎯 Target Macro F1-Score: {target:.2f}")
    print(f"     Achieved: {macro['f1']:.4f} {'✅ PASS' if macro['f1'] >= target else '❌ FAIL'}")
    print("="*70)


def save_metrics(metrics, output_path, model_name):
    """Save metrics to JSON file"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    output = {
        'model': model_name,
        'metrics': metrics
    }
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n  ✅ Metrics saved: {output_path}")


def print_confusion_summary(metrics, model_name="Model"):
    """Print TP/FP/FN summary"""
    print(f"\n  📋 ERROR ANALYSIS - {model_name}")
    print("  " + "-"*60)
    print(f"  {'Entity':<12} {'TP':>6} {'FP':>6} {'FN':>6} {'Total':>8}")
    print("  " + "-"*60)
    
    entity_types = sorted([k for k in metrics.keys() if not k.startswith('_')])
    
    for ent in entity_types:
        m = metrics[ent]
        total = m['tp'] + m['fn']
        print(f"  {ent:<12} {m['tp']:>6} {m['fp']:>6} {m['fn']:>6} {total:>8}")


# === DEMO ===
def demo():
    """Test evaluator dengan dummy data"""
    print("="*65)
    print("  🧪 EVALUATOR - DEMO")
    print("="*65)
    
    # Dummy data
    tokens = [['Budi', 'lahir', 'di', 'Jakarta'], 
              ['NIK', '3201234567890123', 'milik', 'Ani']]
    
    y_true = [['B-NAMA', 'O', 'O', 'B-LOKASI'],
              ['O', 'B-NIK', 'O', 'B-NAMA']]
    
    y_pred = [['B-NAMA', 'O', 'O', 'B-LOKASI'],  # Perfect
              ['O', 'B-NIK', 'O', 'O']]  # Missed NAMA
    
    metrics = compute_entity_metrics(y_true, y_pred, tokens)
    print_classification_report(metrics, "Demo Model")
    print_confusion_summary(metrics, "Demo Model")


if __name__ == "__main__":
    demo()