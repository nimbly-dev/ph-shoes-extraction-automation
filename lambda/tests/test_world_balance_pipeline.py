# tests/test_world_balance_pipeline.py

import os
import sys

# ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(__file__, os.pardir, "..")))

import pandas as pd

from extractors.world_balance import WorldBalanceExtractor, product_lists_url
from clean.worldbalance     import WorldBalanceCleaner
from quality.worldbalance    import WorldBalanceQuality

def test_world_balance_pipeline():
    cleaner = WorldBalanceCleaner()
    tester  = WorldBalanceQuality()

    for path in product_lists_url:
        print(f"\n=== Testing WorldBalance category: {path} ===")

        # 1) Extract
        extractor = WorldBalanceExtractor(category=path, num_pages=-1)
        shoes     = extractor.extract()
        print(f"Extracted {len(shoes)} raw records from {path}")

        # 2) Clean
        raw_dicts = [s.__dict__ for s in shoes]
        df_raw    = pd.DataFrame(raw_dicts)
        df_clean  = cleaner.clean(df_raw)
        print(f"Cleaned down to {len(df_clean)} records")

        # 3) Quality
        overall, results = tester.run(df_clean)
        print(f"Quality results for {path}: {results}")
        assert overall, f"QA failed for WorldBalance category {path}"

    print("\n✅ All WorldBalance categories extracted, cleaned, and passed QA.")

if __name__ == "__main__":
    test_world_balance_pipeline()
