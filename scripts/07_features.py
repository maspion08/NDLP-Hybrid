"""
Feature Engineering untuk Model Statistik (HMM, CRF, dan Hybrid)
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Sesuai Bab III.3.c.3 Proposal:
- Word identity & konteks ±2 token
- Prefix/suffix 1-4 karakter
- Word shape (pola karakter)
- Posisi token dalam kalimat
- Regex-as-a-Feature (untuk model hybrid)

File ini menjadi dependency untuk:
- 11_train_hmm.py
- 12_train_crf.py
- 13_train_hybrid_hmm.py
- 14_train_hybrid_crf.py
"""
import re


# Pola Regex untuk Regex-as-a-Feature
PATTERN_NIK = re.compile(r'^\d{16}$')
PATTERN_PHONE = re.compile(r'^(?:\+62|0)\d{8,12}$')


def get_word_shape(word):
    """
    Ekstrak word shape pattern.
    Contoh:
        'Budi'        -> 'Xxxx'
        'NIK'         -> 'XXX'
        '081234567'   -> 'ddddddddd'
        'Bagian2'     -> 'Xxxxxxd'
    """
    shape = []
    for char in word:
        if char.isupper():
            shape.append('X')
        elif char.islower():
            shape.append('x')
        elif char.isdigit():
            shape.append('d')
        else:
            shape.append(char)
    return ''.join(shape)


def get_short_word_shape(word):
    """Word shape dengan repeat character collapsed (Xx vs Xxxxxx)"""
    shape = get_word_shape(word)
    # Collapse: 'Xxxxxx' -> 'Xx', 'ddddd' -> 'd'
    short = []
    prev = None
    for char in shape:
        if char != prev:
            short.append(char)
            prev = char
    return ''.join(short)


def has_digit(word):
    """Check if word contains any digit"""
    return any(c.isdigit() for c in word)


def is_all_digits(word):
    """Check if word is purely digits"""
    return word.isdigit()


def is_all_caps(word):
    """Check if word is all uppercase"""
    return word.isupper() and len(word) > 1


def is_capitalized(word):
    """Check if word starts with uppercase"""
    return len(word) > 0 and word[0].isupper()


def matches_nik_pattern(word):
    """Regex feature: apakah token cocok pola NIK?"""
    return bool(PATTERN_NIK.match(word))


def matches_phone_pattern(word):
    """Regex feature: apakah token cocok pola Phone?"""
    return bool(PATTERN_PHONE.match(word))


def word_to_features(tokens, i, use_regex_features=False):
    """
    Ekstrak fitur untuk token pada posisi i.
    
    Args:
        tokens: list of tokens
        i: posisi token saat ini
        use_regex_features: jika True, tambahkan Regex-as-a-Feature
                           (untuk model hybrid)
    
    Returns:
        dict: feature dictionary
    """
    word = tokens[i]
    
    features = {
        # === FITUR DASAR (proposal: word identity) ===
        'bias': 1.0,
        'word.lower()': word.lower(),
        'word[-3:]': word[-3:],
        'word[-2:]': word[-2:],
        'word[-1:]': word[-1:],
        'word[:3]': word[:3],
        'word[:2]': word[:2],
        'word[:1]': word[:1],
        
        # === WORD SHAPE FEATURES ===
        'word.shape': get_word_shape(word),
        'word.short_shape': get_short_word_shape(word),
        
        # === CHARACTER FEATURES ===
        'word.isupper()': is_all_caps(word),
        'word.islower()': word.islower(),
        'word.istitle()': is_capitalized(word),
        'word.isdigit()': is_all_digits(word),
        'word.has_digit()': has_digit(word),
        
        # === LENGTH FEATURE ===
        'word.length': len(word),
    }
    
    # === FITUR KONTEKS (proposal: konteks ±2 token) ===
    # Token sebelumnya (i-1)
    if i > 0:
        prev_word = tokens[i-1]
        features.update({
            '-1:word.lower()': prev_word.lower(),
            '-1:word.istitle()': is_capitalized(prev_word),
            '-1:word.isupper()': is_all_caps(prev_word),
            '-1:word.isdigit()': is_all_digits(prev_word),
            '-1:word.shape': get_word_shape(prev_word),
        })
    else:
        features['BOS'] = True  # Beginning of Sequence
    
    # Token sebelumnya (i-2)
    if i > 1:
        prev2_word = tokens[i-2]
        features.update({
            '-2:word.lower()': prev2_word.lower(),
            '-2:word.istitle()': is_capitalized(prev2_word),
        })
    
    # Token setelahnya (i+1)
    if i < len(tokens) - 1:
        next_word = tokens[i+1]
        features.update({
            '+1:word.lower()': next_word.lower(),
            '+1:word.istitle()': is_capitalized(next_word),
            '+1:word.isupper()': is_all_caps(next_word),
            '+1:word.isdigit()': is_all_digits(next_word),
            '+1:word.shape': get_word_shape(next_word),
        })
    else:
        features['EOS'] = True  # End of Sequence
    
    # Token setelahnya (i+2)
    if i < len(tokens) - 2:
        next2_word = tokens[i+2]
        features.update({
            '+2:word.lower()': next2_word.lower(),
            '+2:word.istitle()': is_capitalized(next2_word),
        })
    
    # === FITUR POSISI ===
    features['position'] = i / len(tokens)  # Normalized position 0-1
    features['position_abs'] = i
    
    # === REGEX-AS-A-FEATURE (untuk Hybrid Model) ===
    if use_regex_features:
        features['regex.is_nik'] = matches_nik_pattern(word)
        features['regex.is_phone'] = matches_phone_pattern(word)
    
    return features


def sentence_to_features(tokens, use_regex_features=False):
    """
    Convert seluruh kalimat (list tokens) ke list of feature dicts.
    
    Args:
        tokens: list of tokens
        use_regex_features: untuk hybrid model
    
    Returns:
        list of feature dicts (1 per token)
    """
    return [word_to_features(tokens, i, use_regex_features) 
            for i in range(len(tokens))]


def sentence_to_labels(labels):
    """Pastikan labels dalam format yang benar (list of strings)"""
    return list(labels)


def dataset_to_features(df, use_regex_features=False, verbose=True):
    """
    Convert dataframe ke format X (features) dan y (labels) untuk training.
    
    Args:
        df: DataFrame dengan kolom 'tokens' dan 'labels'
        use_regex_features: untuk hybrid model
        verbose: print progress
    
    Returns:
        X: list of list of feature dicts
        y: list of list of labels
    """
    if verbose:
        print(f"  Extracting features (regex={use_regex_features})...")
    
    X = []
    y = []
    
    for _, row in df.iterrows():
        tokens = row['tokens']
        labels = row['labels']
        
        x_seq = sentence_to_features(tokens, use_regex_features)
        y_seq = sentence_to_labels(labels)
        
        X.append(x_seq)
        y.append(y_seq)
    
    if verbose:
        print(f"  Done: {len(X)} sequences")
    
    return X, y


# === DEMO / TEST ===
def demo():
    """Test feature extraction dengan contoh"""
    print("="*65)
    print("  🧪 FEATURE ENGINEERING - DEMO")
    print("="*65)
    
    # Test tokens
    test_tokens = ['Permohonan', 'untuk', 'Budi', 'dengan', 'NIK', 
                   '3201234567890123', 'sebagai', 'Camat', 'di', 'Jakarta']
    
    print(f"\n  Test tokens: {test_tokens}\n")
    
    # Tanpa regex feature
    print("  📌 BASIC FEATURES (untuk HMM/CRF Murni):")
    print("  " + "-"*61)
    features = word_to_features(test_tokens, 5, use_regex_features=False)
    print(f"  Token: '{test_tokens[5]}' (position 5 - NIK)")
    print(f"  Features ({len(features)} total):")
    for k, v in list(features.items())[:10]:
        print(f"     {k:<25}: {v}")
    print(f"     ... (and {len(features) - 10} more)")
    
    # Dengan regex feature (hybrid)
    print(f"\n  📌 WITH REGEX FEATURES (untuk Hybrid HMM/CRF):")
    print("  " + "-"*61)
    features_hybrid = word_to_features(test_tokens, 5, use_regex_features=True)
    print(f"  Token: '{test_tokens[5]}' (NIK)")
    print(f"  Regex features:")
    print(f"     regex.is_nik   : {features_hybrid['regex.is_nik']}")
    print(f"     regex.is_phone : {features_hybrid['regex.is_phone']}")
    
    # Test phone token
    print(f"\n  Token: '081234567890' (Phone)")
    phone_tokens = ['HP', ':', '081234567890']
    features_phone = word_to_features(phone_tokens, 2, use_regex_features=True)
    print(f"     regex.is_nik   : {features_phone['regex.is_nik']}")
    print(f"     regex.is_phone : {features_phone['regex.is_phone']}")
    
    # Test word shape
    print(f"\n  📌 WORD SHAPE EXAMPLES:")
    print("  " + "-"*61)
    test_words = ['Budi', 'NIK', '081234', 'Jakarta2024', 'hello']
    for w in test_words:
        print(f"     '{w:<15}' -> shape: '{get_word_shape(w):<15}' "
              f"short: '{get_short_word_shape(w)}'")
    
    print("\n" + "="*65)
    print("  ✅ Feature engineering ready")
    print("="*65)


if __name__ == "__main__":
    demo()