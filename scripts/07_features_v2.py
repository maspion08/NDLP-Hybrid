"""
Feature Engineering v2 untuk Hybrid CRF
Tugas Akhir: Arga Ariyuda Avian (2221101774)

LANDASAN ILMIAH:
================
1. Tjong Kim Sang & De Meulder (2003) CoNLL-2003:
   - Word identity, prefix/suffix, word shape features
   
2. Huang et al. (2015) BiLSTM-CRF:
   - Gazetteer features boost NER accuracy

3. Srihari (2000) Hybrid NER:
   - Rule + gazetteer + statistical = best

4. Domain-specific features (Payment NER 2026):
   - +5.2 F1 point improvement dari pattern + field type features

STRATEGI v2 FEATURES (Total ~50 fitur):
=======================================
A. Existing features (29) - dari v1
B. Context-aware regex (4) - LABEL detection
C. Structural validation (3) - NIK structure
D. Gazetteer lookup (5) - dictionary
E. Negative context (2) - anti-FP KILLER FEATURE
F. N-gram patterns (2) - multi-token

TOTAL: ~45 features per token
"""
from nik_utils import validate_nik_structure, nik_structure_score
import os
import json
import re

# ============================================================
# LOAD GAZETTEER
# ============================================================
GAZETTEER_PATH = 'data/gazetteer/gazetteer.json'

if os.path.exists(GAZETTEER_PATH):
    with open(GAZETTEER_PATH, 'r', encoding='utf-8') as f:
        GAZETTEER = json.load(f)
    
    JABATAN_TOKENS = set(GAZETTEER['jabatan_tokens'])
    JABATAN_PHRASES = set(GAZETTEER['jabatan_phrases'])
    JABATAN_PREFIX = set(GAZETTEER['jabatan_prefix'])
    LOKASI_TOKENS = set(GAZETTEER['lokasi_tokens'])
    LOKASI_PHRASES = set(GAZETTEER['lokasi_phrases'])
    NAMA_PREFIXES = set(GAZETTEER['nama_prefixes'])
    NIK_LABELS = set(GAZETTEER['nik_labels'])
    PHONE_LABELS = set(GAZETTEER['phone_labels'])
    NEGATIVE_KEYWORDS = set(GAZETTEER['negative_keywords'])
else:
    print("⚠️ Gazetteer not found! Run 25_build_gazetteer.py first")
    JABATAN_TOKENS = JABATAN_PHRASES = JABATAN_PREFIX = set()
    LOKASI_TOKENS = LOKASI_PHRASES = set()
    NAMA_PREFIXES = NIK_LABELS = PHONE_LABELS = NEGATIVE_KEYWORDS = set()

# ============================================================
# REGEX PATTERNS
# ============================================================
PATTERN_NIK_16DIGIT = re.compile(r'^\d{16}$')
PATTERN_PHONE = re.compile(r'^(?:\+62|0)\d{8,12}$')

# Phone prefix validation (Indonesia)
INDONESIAN_PHONE_PREFIXES = {
    '0811', '0812', '0813', '0814', '0815', '0816', '0817', '0818', '0819',
    '0821', '0822', '0823', '0851', '0852', '0853', '0855', '0856', '0857', '0858',
    '+6281', '+6282', '+6285', '+6287'
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_word_shape(word):
    """Word shape: d=digit, X=upper, x=lower, .=other"""
    shape = ''
    for c in word:
        if c.isdigit():
            shape += 'd'
        elif c.isupper():
            shape += 'X'
        elif c.islower():
            shape += 'x'
        else:
            shape += '.'
    return shape


def get_word_shape_simple(word):
    """Simplified word shape: collapse consecutive same characters"""
    shape = get_word_shape(word)
    simplified = ''
    prev = ''
    for c in shape:
        if c != prev:
            simplified += c
        prev = c
    return simplified


def validate_nik_structure(token):
    """
    Validate NIK structure berdasarkan format Indonesia:
    - 16 digit total
    - Provinsi 11-94
    - Tanggal: 1-31 (perempuan +40, jadi 41-71)
    - Bulan: 1-12
    """
    if not (len(token) == 16 and token.isdigit()):
        return False, False, False
    
    try:
        provinsi = int(token[0:2])
        tanggal = int(token[6:8])
        bulan = int(token[8:10])
        
        prov_valid = 11 <= provinsi <= 94
        tanggal_valid = (1 <= tanggal <= 31) or (41 <= tanggal <= 71)
        bulan_valid = 1 <= bulan <= 12
        
        return True, prov_valid, (tanggal_valid and bulan_valid)
    except:
        return False, False, False


def validate_phone_prefix(token):
    """Check apakah phone prefix valid Indonesia"""
    # Strip +62 or leading 0
    if token.startswith('+62'):
        prefix = token[:5]  # +6281, +6282, dll
    elif token.startswith('0'):
        prefix = token[:4]  # 0811, 0812, dll
    else:
        return False
    
    return prefix in INDONESIAN_PHONE_PREFIXES


def has_negative_context(tokens, idx, window=10):
    """Check apakah ada negative keyword di context (±3 token)"""
    start = max(0, idx - window)
    end = min(len(tokens), idx + window + 1)
    
    for i in range(start, end):
        if i == idx:
            continue
        tok_lower = tokens[i].lower()
        # Strip punctuation untuk matching
        tok_clean = re.sub(r'[^\w]', '', tok_lower)
        if tok_clean in NEGATIVE_KEYWORDS:
            return True
        # Check juga compound words
        for neg_kw in NEGATIVE_KEYWORDS:
            if neg_kw in tok_lower:
                return True
    return False


def has_nik_label(tokens, idx, window=10):
    """Check apakah ada NIK label keyword di context sebelumnya"""
    start = max(0, idx - window)
    for i in range(start, idx):
        tok_lower = tokens[i].lower()
        tok_clean = re.sub(r'[^\w]', '', tok_lower)
        if tok_clean in NIK_LABELS:
            return True
    return False


def has_phone_label(tokens, idx, window=10):
    """Check apakah ada PHONE label keyword di context sebelumnya"""
    start = max(0, idx - window)
    for i in range(start, idx):
        tok_lower = tokens[i].lower()
        tok_clean = re.sub(r'[^\w]', '', tok_lower)
        if tok_clean in PHONE_LABELS:
            return True
    return False


def is_in_form_field_position(tokens, idx):
    """Check apakah token berada setelah pattern 'Label : ' (form field)"""
    if idx < 2:
        return False
    # Pattern: <label> : <value>
    prev1 = tokens[idx-1]
    prev2 = tokens[idx-2] if idx >= 2 else ''
    
    if prev1 in [':', '=']:
        # Previous token is delimiter, prev-prev is label
        return prev2.isalpha() or '_' in prev2
    return False


# ============================================================
# MAIN FEATURE EXTRACTOR
# ============================================================

def token_to_features_v2(tokens, idx, use_regex_features=True, use_gazetteer=True):
    """
    Extract rich features untuk satu token.
    
    Args:
        tokens: list of tokens dalam satu sentence
        idx: index token saat ini
        use_regex_features: pakai context-aware regex features
        use_gazetteer: pakai gazetteer features
    
    Returns:
        dict of features
    """
    word = tokens[idx]
    
    # ====================================================
    # A. EXISTING FEATURES (29 fitur) - dari v1
    # ====================================================
    features = {
        'bias': 1.0,
        'word.identity': word,
        'word.lower': word.lower(),
        'word.shape': get_word_shape(word),
        'word.shape_simple': get_word_shape_simple(word),
        'word.isupper': word.isupper(),
        'word.istitle': word.istitle(),
        'word.isdigit': word.isdigit(),
        'word.length': len(word),
    }
    
    # Prefix and Suffix
    for n in [2, 3, 4]:
        features[f'word.prefix-{n}'] = word[:n].lower() if len(word) >= n else word.lower()
        features[f'word.suffix-{n}'] = word[-n:].lower() if len(word) >= n else word.lower()
    
    # Context features (left)
    if idx > 0:
        prev_word = tokens[idx-1]
        features.update({
            '-1:word.lower': prev_word.lower(),
            '-1:word.shape': get_word_shape(prev_word),
            '-1:word.istitle': prev_word.istitle(),
            '-1:word.isupper': prev_word.isupper(),
        })
    else:
        features['BOS'] = True
    
    if idx > 1:
        prev2_word = tokens[idx-2]
        features['-2:word.lower'] = prev2_word.lower()
        features['-2:word.shape'] = get_word_shape(prev2_word)
    
    # Context features (right)
    if idx < len(tokens) - 1:
        next_word = tokens[idx+1]
        features.update({
            '+1:word.lower': next_word.lower(),
            '+1:word.shape': get_word_shape(next_word),
            '+1:word.istitle': next_word.istitle(),
            '+1:word.isupper': next_word.isupper(),
        })
    else:
        features['EOS'] = True
    
    if idx < len(tokens) - 2:
        next2_word = tokens[idx+2]
        features['+2:word.lower'] = next2_word.lower()
        features['+2:word.shape'] = get_word_shape(next2_word)
    
    # ====================================================
    # B. CONTEXT-AWARE REGEX FEATURES (4 fitur) - NEW!
    # ====================================================
    if use_regex_features:
        # B.1 Basic regex match
        features['regex.matches_nik_pattern'] = bool(PATTERN_NIK_16DIGIT.match(word))
        features['regex.matches_phone_pattern'] = bool(PATTERN_PHONE.match(word))
        
        # B.2 Context label detection
        features['regex.has_nik_label_context'] = has_nik_label(tokens, idx)
        features['regex.has_phone_label_context'] = has_phone_label(tokens, idx)
        
        # B.3 Form field position
        features['regex.in_form_field_position'] = is_in_form_field_position(tokens, idx)
        
        # ====================================================
        # C. STRUCTURAL VALIDATION (3 fitur) - NEW!
        # ====================================================
        if features['regex.matches_nik_pattern']:
            is_16d, prov_valid, date_valid = validate_nik_structure(word)
            features['regex.nik_structure_complete'] = is_16d and prov_valid and date_valid
            features['regex.nik_province_valid'] = prov_valid
            features['regex.nik_date_valid'] = date_valid
        else:
            features['regex.nik_structure_complete'] = False
            features['regex.nik_province_valid'] = False
            features['regex.nik_date_valid'] = False
        
        if features['regex.matches_phone_pattern']:
            features['regex.phone_valid_prefix'] = validate_phone_prefix(word)
        else:
            features['regex.phone_valid_prefix'] = False
        
        # ====================================================
        # E. NEGATIVE CONTEXT FEATURES (2 fitur) - KILLER!
        # ====================================================
        # Anti-False-Positive untuk NIK dan PHONE
        if features['regex.matches_nik_pattern']:
            features['regex.nik_has_negative_context'] = has_negative_context(tokens, idx)
        else:
            features['regex.nik_has_negative_context'] = False
        
        if features['regex.matches_phone_pattern']:
            features['regex.phone_has_negative_context'] = has_negative_context(tokens, idx)
        else:
            features['regex.phone_has_negative_context'] = False
    
    # ====================================================
    # D. GAZETTEER FEATURES (5 fitur) - NEW!
    # ====================================================
    if use_gazetteer:
        word_lower = word.lower()
        
        # D.1 JABATAN gazetteer
        features['gazetteer.in_jabatan_dict'] = word_lower in JABATAN_TOKENS
        features['gazetteer.is_jabatan_prefix'] = word_lower in JABATAN_PREFIX
        
        # D.2 LOKASI gazetteer
        features['gazetteer.in_lokasi_dict'] = word_lower in LOKASI_TOKENS
        
        # D.3 NAMA gazetteer
        features['gazetteer.in_nama_dict'] = word_lower in NAMA_PREFIXES
        
        # D.4 Gelar marker (S.E., M.Sc., Dr., etc)
        gelar_markers = ['S.', 'M.', 'Dr.', 'Drs.', 'Hj.', 'H.', 'Ir.', 'Prof.', 'Ph.D']
        features['gazetteer.has_gelar_marker'] = any(g in word for g in gelar_markers)
        
        # ====================================================
        # F. N-GRAM PATTERN FEATURES (2 fitur) - NEW!
        # ====================================================
        # F.1 Bigram JABATAN pattern (e.g., "Kepala Dinas")
        if idx < len(tokens) - 1:
            bigram = f"{word.lower()} {tokens[idx+1].lower()}"
            features['ngram.bigram_jabatan_phrase'] = bigram in JABATAN_PHRASES
        else:
            features['ngram.bigram_jabatan_phrase'] = False
        
        # F.2 Bigram LOKASI pattern (e.g., "Jawa Barat")
        if idx < len(tokens) - 1:
            bigram = f"{word.lower()} {tokens[idx+1].lower()}"
            features['ngram.bigram_lokasi_phrase'] = bigram in LOKASI_PHRASES
        else:
            features['ngram.bigram_lokasi_phrase'] = False
    
    return features


def sentence_to_features_v2(tokens, use_regex_features=True, use_gazetteer=True):
    """Extract features untuk seluruh sentence"""
    return [token_to_features_v2(tokens, i, use_regex_features, use_gazetteer) 
            for i in range(len(tokens))]


def dataset_to_features_v2(df, use_regex_features=True, use_gazetteer=True, verbose=True):
    """Extract features untuk seluruh dataset"""
    if verbose:
        print(f"  Extracting v2 features (regex={use_regex_features}, gazetteer={use_gazetteer})...")
    
    X = [sentence_to_features_v2(tokens, use_regex_features, use_gazetteer) 
         for tokens in df['tokens']]
    y = [labels for labels in df['labels']]
    
    if verbose:
        print(f"  Done: {len(X)} sequences")
        if X and len(X[0]) > 0:
            print(f"  Features per token: {len(X[0][0])}")
    
    return X, y


if __name__ == "__main__":
    # Quick test
    test_tokens = ['NIK', ':', '3201234567890123', 'milik', 'Budi', 'Santoso']
    features = sentence_to_features_v2(test_tokens)
    
    print("="*70)
    print("  🧪 FEATURE EXTRACTOR v2 TEST")
    print("="*70)
    print(f"\nTokens: {test_tokens}")
    print(f"\nNumber of tokens: {len(features)}")
    print(f"Features per token: {len(features[0])}")
    print(f"\nFeatures for token '3201234567890123':")
    for k, v in sorted(features[2].items()):
        if isinstance(v, bool) and v:
            print(f"  ✅ {k}: {v}")
        elif not isinstance(v, bool):
            print(f"  📝 {k}: {v}")