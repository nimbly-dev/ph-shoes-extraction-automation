# tests/test_hoka_pipeline.py

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(__file__, os.pardir, "..")))

import json
import pandas as pd

from handlers.extract import lambda_handler as extract_lambda
from clean.hoka    import HokaCleaner
from quality.hoka  import HokaQuality

def test_hoka():
    # 1) Extract phase via your extract Lambda
    extract_event = {
        "queryStringParameters": {
            "brand":    "hoka",
            "category": "/mens-road",
            "pages":    "-1"
        }
    }
    resp = extract_lambda(extract_event, None)
    assert resp["statusCode"] == 200, resp
    body = json.loads(resp["body"])
    raw = body["extracted"]
    print(f"Extracted {len(raw)} records")

    # 2) Clean phase by directly invoking your HokaCleaner
    df_raw = pd.DataFrame(raw)
    cleaner = HokaCleaner()
    df_clean = cleaner.clean(df_raw)
    clean_records = df_clean.to_dict(orient="records")
    print(f"Cleaned down to {len(clean_records)} records")

    # 3) Quality phase by directly invoking your HokaQuality
    tester = HokaQuality()
    overall, results = tester.run(df_clean)
    print("Quality results:", json.dumps({"overall": overall, "checks": results}, indent=2))

    assert overall, "One or more quality checks failed"

if __name__ == "__main__":
    test_hoka()
