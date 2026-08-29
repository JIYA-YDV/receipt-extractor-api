"""Run every eval case through the endpoint and score it accurately."""
import json
import sys
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.llm.call import extract_with_llm
from src.llm.prompt import PROMPT_VERSION

CASES_PATH = Path(__file__).parent / "cases.json"


def check_case(expected: dict, actual: dict) -> tuple[bool, list[str]]:
    """Return (passed, list_of_failure_reasons)."""
    failures = []

    # Check merchant substring
    if "merchant_contains" in expected:
        m = actual.get("merchant") or ""
        if expected["merchant_contains"].lower() not in m.lower():
            failures.append(f"merchant '{m}' does not contain '{expected['merchant_contains']}'")

    # Check exact merchant (including None)
    if "merchant" in expected:
        if actual.get("merchant") != expected["merchant"]:
            failures.append(f"merchant={actual.get('merchant')} (expected {expected['merchant']})")

    # Check total (handles None vs numeric values)
    if "total" in expected:
        exp_total = expected["total"]
        act_total = actual.get("total")
        if exp_total is None:
            if act_total is not None:
                failures.append(f"total={act_total} (expected None)")
        else:
            if act_total is None:
                failures.append(f"total is None (expected {exp_total})")
            else:
                try:
                    if abs(float(act_total) - float(exp_total)) > 0.01:
                        failures.append(f"total={act_total} (expected {exp_total})")
                except (ValueError, TypeError):
                    failures.append(f"total={act_total} not comparable to {exp_total}")

    # Check currency
    if "currency" in expected:
        if actual.get("currency") != expected["currency"]:
            failures.append(f"currency={actual.get('currency')} (expected {expected['currency']})")

    # Check date (handles None vs exact string)
    if "date" in expected:
        exp_date = expected["date"]
        act_date = actual.get("date")
        if act_date != exp_date:
            failures.append(f"date={act_date} (expected {exp_date})")

    # Check needs_review flag
    if "needs_review" in expected:
        if actual.get("needs_review") != expected["needs_review"]:
            failures.append(f"needs_review={actual.get('needs_review')} (expected {expected['needs_review']})")

    # Check confidence threshold
    if "confidence_below" in expected:
        c = actual.get("confidence", 1.0)
        if c >= expected["confidence_below"]:
            failures.append(f"confidence={c} (expected below {expected['confidence_below']})")

    return len(failures) == 0, failures


def main():
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    passed = 0
    total = len(cases)
    failed_cases = []

    print(f"Running {total} eval cases against prompt '{PROMPT_VERSION}'...\n")

    for case in cases:
        name = case["name"]
        try:
            result, repair_count = extract_with_llm(case["input"])
            actual = json.loads(result.model_dump_json())
            ok, reasons = check_case(case["expected"], actual)
            status = "PASS" if ok else "FAIL"
            repair_note = " (repaired)" if repair_count > 0 else ""
            print(f"[{status}] {name}{repair_note}")
            if ok:
                passed += 1
            else:
                for r in reasons:
                    print(f"       - {r}")
                failed_cases.append(name)
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            failed_cases.append(name)

    print(f"\n{'=' * 50}")
    print(f"Score: {passed}/{total} ({100 * passed / total:.0f}%)")
    print(f"Prompt version: {PROMPT_VERSION}")
    if failed_cases:
        print(f"Failed: {', '.join(failed_cases)}")


if __name__ == "__main__":
    main()