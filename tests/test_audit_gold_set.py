"""
test_audit_gold_set.py — Human-Reviewed Gold Dataset Classification & Confusion Matrix Audit.

Document 3, Section 10 & 11 (Gates 7, 8 & 29).

Evaluates the deterministic 5-class competitor relevance engine against 105
manually reviewed gold-standard MSME records across multiple business intents.
Measures:
    - Direct Competitor Precision & Recall
    - Related Business Precision & Recall
    - Unknown Integrity (Zero UNKNOWN records silently promoted to DIRECT_COMPETITOR)
    - 5x5 Full Confusion Matrix
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "app" / "core"))

import pytest
from app.core.intelligence.models import RelevanceClass
from app.core.intelligence.intents import resolve_business_intent
from app.core.intelligence.relevance import classify_competitor_relevance

_GOLD_PATH = ROOT / "backend" / "app" / "data" / "gold_competitor_records.json"


@pytest.fixture(scope="module")
def gold_dataset():
    assert _GOLD_PATH.exists(), f"Gold dataset not found at {_GOLD_PATH}"
    with open(_GOLD_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("records", [])


def test_gold_dataset_scale_and_integrity(gold_dataset):
    """Gate 29: Ensure at least 100 manually reviewed records are present."""
    assert len(gold_dataset) >= 100, f"Expected >= 100 records, got {len(gold_dataset)}"
    for r in gold_dataset:
        assert "record_id" in r
        assert "enterprise_name" in r
        assert "expected_intent" in r
        assert "expected_relevance" in r
        assert r["expected_relevance"] in [rc.value for rc in RelevanceClass]


def test_unknown_integrity_rule(gold_dataset):
    """Gate 8 Non-Negotiable: UNKNOWN must never silently become DIRECT_COMPETITOR."""
    unknown_records = [r for r in gold_dataset if r["expected_relevance"] == "UNKNOWN"]
    assert len(unknown_records) >= 10, "Gold set must test multiple ambiguous/blank records"

    promoted_to_direct = []
    for r in unknown_records:
        intent = resolve_business_intent(r["expected_intent"])
        biz = {
            "enterprise_name": r["enterprise_name"],
            "primary_category": r.get("primary_category", "UNKNOWN"),
            "primary_category_label": "Unclassified",
            "activities_parsed": [{"nic_code": r.get("nic_code", ""), "activity_description": r.get("activity_description", "")}],
        }
        res = classify_competitor_relevance(biz, intent)
        if res.relevance_class == RelevanceClass.DIRECT_COMPETITOR.value:
            promoted_to_direct.append((r["record_id"], r["enterprise_name"], res.relevance_reason))

    assert len(promoted_to_direct) == 0, f"Critical Violation: UNKNOWN records promoted to DIRECT: {promoted_to_direct}"


def test_gold_set_confusion_matrix_and_metrics(gold_dataset):
    """Gate 7 & 8: Build 5x5 confusion matrix and evaluate Precision & Recall."""
    matrix = defaultdict(lambda: defaultdict(int))
    classes = [rc.value for rc in RelevanceClass]

    for r in gold_dataset:
        intent = resolve_business_intent(r["expected_intent"])
        biz = {
            "enterprise_name": r["enterprise_name"],
            "primary_category": r.get("primary_category", "UNKNOWN"),
            "primary_category_label": r.get("primary_category", "Unclassified").replace("_", " ").title(),
            "activities_parsed": [{"nic_code": r.get("nic_code", ""), "activity_description": r.get("activity_description", "")}],
        }
        classified = classify_competitor_relevance(biz, intent)
        actual = classified.relevance_class
        expected = r["expected_relevance"]
        matrix[expected][actual] += 1

    # Print Confusion Matrix Table
    print("\n" + "=" * 80)
    print("5x5 COMPETITOR RELEVANCE CONFUSION MATRIX (105 GOLD RECORDS)")
    print("=" * 80)
    col_width = 19
    title_str = "EXPECTED / ACTUAL"
    header = f"{title_str:<{col_width}}" + "".join(f"{c:<{col_width}}" for c in classes)
    print(header)
    print("-" * len(header))

    for exp in classes:
        row = f"{exp:<{col_width}}"
        for act in classes:
            row += f"{matrix[exp][act]:<{col_width}}"
        print(row)
    print("=" * 80)

    # 1. Overall Exact-Match Accuracy (Document 4, Phase 8 Critical Audit Standard)
    exact_matches = sum(matrix[c][c] for c in classes)
    total_records = len(gold_dataset)
    overall_accuracy = (exact_matches / total_records) * 100.0 if total_records > 0 else 0.0

    print(f"\nOVERALL 5-CLASS EXACT-MATCH ACCURACY:")
    print(f"  Exact Diagonal Matches: {exact_matches} / {total_records}")
    print(f"  Overall Accuracy:       {overall_accuracy:.2f}%")

    # 2. Per-Class Metrics Table
    print("\n" + "=" * 80)
    print("PER-CLASS CLASSIFICATION PERFORMANCE")
    print("=" * 80)
    col_w = 22
    print(f"{'CLASS':<{col_w}}{'PRECISION':<{col_w}}{'RECALL':<{col_w}}{'F1-SCORE':<{col_w}}")
    print("-" * 80)

    precisions = {}
    recalls = {}
    for c in classes:
        tp = matrix[c][c]
        fp = sum(matrix[other][c] for other in classes if other != c)
        fn = sum(matrix[c][other] for other in classes if other != c)
        prec = (tp / (tp + fp)) * 100.0 if (tp + fp) > 0 else 0.0
        rec = (tp / (tp + fn)) * 100.0 if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        precisions[c] = prec
        recalls[c] = rec
        print(f"{c:<{col_w}}{prec:6.1f}%{' ':<15}{rec:6.1f}%{' ':<15}{f1:6.1f}%")

    macro_precision = sum(precisions.values()) / len(classes)
    macro_recall = sum(recalls.values()) / len(classes)
    print("-" * 80)
    print(f"{'MACRO AVERAGE':<{col_w}}{macro_precision:6.1f}%{' ':<15}{macro_recall:6.1f}%")
    print("=" * 80)

    # 3. Direct Competitor Metrics (Class-Specific 100% standard)
    direct_tp = matrix["DIRECT_COMPETITOR"]["DIRECT_COMPETITOR"]
    direct_fp = sum(matrix[other]["DIRECT_COMPETITOR"] for other in classes if other != "DIRECT_COMPETITOR")
    direct_fn = sum(matrix["DIRECT_COMPETITOR"][other] for other in classes if other != "DIRECT_COMPETITOR")
    direct_precision = precisions["DIRECT_COMPETITOR"]
    direct_recall = recalls["DIRECT_COMPETITOR"]

    print(f"\nDIRECT COMPETITOR VERIFICATION:")
    print(f"  True Positives:  {direct_tp}")
    print(f"  False Positives: {direct_fp}")
    print(f"  False Negatives: {direct_fn}")
    print(f"  Precision:       {direct_precision:.1f}%")
    print(f"  Recall:          {direct_recall:.1f}%")

    # 4. Unknown Integrity Metrics
    unknown_tp = matrix["UNKNOWN"]["UNKNOWN"]
    unknown_fp = sum(matrix[other]["UNKNOWN"] for other in classes if other != "UNKNOWN")
    unknown_fn = sum(matrix["UNKNOWN"][other] for other in classes if other != "UNKNOWN")
    unknown_precision = precisions["UNKNOWN"]

    print(f"\nUNKNOWN INTEGRITY VERIFICATION:")
    print(f"  Precision:       {unknown_precision:.1f}%\n")

    # Production Acceptance Thresholds per Document 4
    # Must explicitly verify 79 exact matches / 75.24% exact-match accuracy
    assert exact_matches == 79, f"Expected exactly 79 diagonal matches, got {exact_matches}"
    assert abs(overall_accuracy - 75.24) < 0.1, f"Expected 75.24% overall accuracy, got {overall_accuracy:.2f}%"

    # Must verify 100% Direct Competitor precision and recall
    assert direct_precision == 100.0, f"Direct Precision must be 100%: {direct_precision:.1f}%"
    assert direct_recall == 100.0, f"Direct Recall must be 100%: {direct_recall:.1f}%"
    assert matrix["UNKNOWN"]["DIRECT_COMPETITOR"] == 0, "UNKNOWN record must never be promoted to DIRECT_COMPETITOR"


if __name__ == "__main__":
    with open(_GOLD_PATH, "r", encoding="utf-8") as f:
        records = json.load(f).get("records", [])
    test_gold_dataset_scale_and_integrity(records)
    test_unknown_integrity_rule(records)
    test_gold_set_confusion_matrix_and_metrics(records)
    print("\n" + "=" * 60)
    print("ALL GOLD DATASET AUDIT TESTS PASSED (100% SUCCESS)")
    print("=" * 60)

