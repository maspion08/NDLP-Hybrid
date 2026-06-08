"""
Environment Test
Tugas Akhir: Arga Ariyuda Avian (2221101774)

Memverifikasi semua dependency terinstall dengan benar
"""
import sys


def get_package_version(package_name):
    """Get package version using importlib.metadata"""
    try:
        import importlib.metadata
        return importlib.metadata.version(package_name)
    except:
        return "unknown"


def test_environment():
    print("="*65)
    print(f"  🐍 Python Version: {sys.version.split()[0]}")
    print(f"  💻 Platform: {sys.platform}")
    print("="*65)
    
    tests = []
    
    # Test 1: Core libraries
    try:
        import numpy as np
        import pandas as pd
        
        if not np.__version__.startswith('1.'):
            print(f"  ❌ NumPy harus 1.x, got {np.__version__}")
            tests.append(False)
        else:
            print(f"  ✅ numpy {np.__version__}")
            print(f"  ✅ pandas {pd.__version__}")
            tests.append(True)
    except Exception as e:
        print(f"  ❌ Core libraries: {e}")
        tests.append(False)
    
    # Test 2: ML libraries (FIXED)
    try:
        import sklearn
        import sklearn_crfsuite
        import hmmlearn
        
        sklearn_ver = sklearn.__version__
        crf_ver = get_package_version('sklearn-crfsuite')
        hmm_ver = hmmlearn.__version__
        
        print(f"  ✅ scikit-learn {sklearn_ver}")
        print(f"  ✅ sklearn-crfsuite {crf_ver}")
        print(f"  ✅ hmmlearn {hmm_ver}")
        
        # Functional test
        from sklearn_crfsuite import CRF
        crf = CRF(algorithm='lbfgs', max_iterations=10)
        
        from hmmlearn import hmm
        model = hmm.CategoricalHMM(n_components=3)
        
        tests.append(True)
    except Exception as e:
        print(f"  ❌ ML libraries: {e}")
        tests.append(False)
    
    # Test 3: Data generation
    try:
        from faker import Faker
        fake = Faker('id_ID')
        sample = fake.name()
        faker_ver = get_package_version('faker')
        print(f"  ✅ faker {faker_ver} (sample: {sample})")
        tests.append(True)
    except Exception as e:
        print(f"  ❌ Faker: {e}")
        tests.append(False)
    
    # Test 4: Utility
    try:
        import tqdm
        import matplotlib
        import seaborn
        print(f"  ✅ tqdm {tqdm.__version__}")
        print(f"  ✅ matplotlib {matplotlib.__version__}")
        print(f"  ✅ seaborn {seaborn.__version__}")
        tests.append(True)
    except Exception as e:
        print(f"  ❌ Utility: {e}")
        tests.append(False)
    
    # Test 5: Dataset accessibility
    try:
        import pandas as pd
        df = pd.read_pickle('data/processed/dataset_bio.pkl')
        print(f"  ✅ Dataset loadable: {len(df)} samples")
        tests.append(True)
    except Exception as e:
        print(f"  ⚠️  Dataset not loaded: {e}")
        # Tidak fail karena dataset bisa belum di-generate
    
    # Final verdict
    print("\n" + "="*65)
    if all(tests):
        print("  ✅ ENVIRONMENT 100% READY")
        print("  ➡️  Lanjut ke training models")
        return True
    else:
        print(f"  ❌ {tests.count(False)}/{len(tests)} tests failed")
        return False


if __name__ == "__main__":
    success = test_environment()
    sys.exit(0 if success else 1)