# tests/test_nike_pipeline.py

import os
import sys

# make sure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(__file__, os.pardir, "..")))

import pandas as pd

from extractors.nike import NikeExtractor
from clean.nike       import NikeCleaner
from quality.nike     import NikeQuality

def test_nike_pipeline():
    cleaner = NikeCleaner()
    tester  = NikeQuality()

    for category in NikeExtractor.PRODUCT_LISTS_URL:
        print(f"\n=== Testing Nike category: {category} ===")

        # 1) Extract
        extractor = NikeExtractor(category, num_pages=-1)
        shoes     = extractor.extract()
        print(f"Extracted {len(shoes)} raw records from {category}")

        # 2) Clean
        # convert dataclasses → dicts → DataFrame
        raw_dicts = [s.__dict__ for s in shoes]
        df_raw    = pd.DataFrame(raw_dicts)
        df_clean  = cleaner.clean(df_raw)
        print(f"Cleaned down to {len(df_clean)} records")

        # 3) Quality
        overall, results = tester.run(df_clean)
        print(f"Quality results for {category}: {results}")
        assert overall, f"QA failed for category {category}"

    print("\n✅ All Nike categories extracted, cleaned, and passed QA.")

if __name__ == "__main__":
    test_nike_pipeline()
