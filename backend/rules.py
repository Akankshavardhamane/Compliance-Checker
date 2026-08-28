"""
Legal Metrology Rule Engine
Evaluates OCR-extracted packaging fields against compliance rules.
Field source: Person 1's finalized OCR contract (6 fields).
"""

import math

CRITICAL_FIELDS = ["mrp", "net_quantity", "consumer_care"]
SUPPORTING_FIELDS = ["mfg_date", "manufacturer_address", "best_before_date"]
POINTS_PER_SUPPORTING_FIELD = 10

FIELD_META = {
    "mrp": {"label": "Max Retail Price (MRP)", "tier": "critical", "rule": "Rule 6(1)(e)"},
    "net_quantity": {"label": "Net Quantity", "tier": "critical", "rule": "Rule 6(1)(b)"},
    "consumer_care": {"label": "Consumer Care Details", "tier": "critical", "rule": "Rule 6(1)(h)"},
    "mfg_date": {"label": "Month & Year of Packing", "tier": "supporting", "rule": "Rule 6(1)(d)"},
    "manufacturer_address": {"label": "Manufacturer Address", "tier": "supporting", "rule": "Rule 6(1)(a)"},
    "best_before_date": {"label": "Best Before Date", "tier": "supporting", "rule": "FSSAI labeling (not LMPC) \u2014 verify"},
    "font_readability": {"label": "Minimum Font Size (MRP / Net Qty)", "tier": "info", "rule": "Rule 7(1)"},
}


def _as_dict(payload):
    """Accepts a dict OR a Pydantic model (e.g. ScanInput) and normalizes to dict."""
    if payload is None:
        return {}
    if hasattr(payload, "dict"):
        return payload.dict()
    return payload


def _field_status(field_data):
    if not isinstance(field_data, dict):
        return False, None
    return bool(field_data.get("detected")), field_data.get("value")


def run_rule_engine(extracted) -> dict:
    extracted = _as_dict(extracted)

    results = []
    critical_fail_fields = []
    supporting_score = 0
    supporting_pool = 0

    for key in CRITICAL_FIELDS:
        detected, value = _field_status(extracted.get(key))
        status = "pass" if detected else "fail"
        if not detected:
            critical_fail_fields.append(key)
        results.append({
            "field": key,
            "label": FIELD_META[key]["label"],
            "tier": "critical",
            "rule": FIELD_META[key]["rule"],
            "status": status,
            "detected_value": value or "Not detected",
        })

    for key in SUPPORTING_FIELDS:
        field_data = extracted.get(key) or {}

        if key == "best_before_date" and field_data.get("applicable") is False:
            results.append({
                "field": key,
                "label": FIELD_META[key]["label"],
                "tier": "supporting",
                "rule": FIELD_META[key]["rule"],
                "status": "not_applicable",
                "detected_value": "N/A \u2014 not applicable to this product",
            })
            continue

        detected, value = _field_status(field_data)
        supporting_pool += POINTS_PER_SUPPORTING_FIELD
        if detected:
            supporting_score += POINTS_PER_SUPPORTING_FIELD

        results.append({
            "field": key,
            "label": FIELD_META[key]["label"],
            "tier": "supporting",
            "rule": FIELD_META[key]["rule"],
            "status": "pass" if detected else "fail",
            "detected_value": value or "Not detected",
        })

    readability_notes = []
    for key in ("mrp", "net_quantity"):
        field_data = extracted.get(key) or {}
        flag = field_data.get("small_text_flag")
        pct = field_data.get("text_height_pct")
        if flag is None or pct is None:
            continue
        readability_notes.append({
            "field": key,
            "label": FIELD_META[key]["label"],
            "text_height_pct": pct,
            "small_text_flag": flag,
        })

    supporting_threshold = math.ceil(supporting_pool * 2 / 3) if supporting_pool else 0
    supporting_pass = supporting_score >= supporting_threshold

    is_critical_fail = len(critical_fail_fields) > 0
    overall_status = "compliant" if (not is_critical_fail and supporting_pass) else "non-compliant"

    violations = []
    for r in results:
        if r["status"] == "fail":
            violations.append({"rule": r["rule"], "description": f"Missing or undetected: {r['label']}"})
    for note in readability_notes:
        if note["small_text_flag"]:
            violations.append({
                "rule": FIELD_META["font_readability"]["rule"],
                "description": f"{note['label']} text below readable size threshold "
                                f"({note['text_height_pct']:.1f}% of image height)",
            })

    critical_passed = len(CRITICAL_FIELDS) - len(critical_fail_fields)
    supporting_passed = supporting_score // POINTS_PER_SUPPORTING_FIELD if POINTS_PER_SUPPORTING_FIELD else 0
    fields_total = len(CRITICAL_FIELDS) + (supporting_pool // POINTS_PER_SUPPORTING_FIELD)
    fields_passed = critical_passed + supporting_passed
    compliance_pct = round(fields_passed / fields_total * 100) if fields_total else 0

    return {
        "field_results": results,
        "readability_notes": readability_notes,
        "critical_fail_fields": critical_fail_fields,
        "supporting_score": supporting_score,
        "supporting_pool": supporting_pool,
        "supporting_threshold": supporting_threshold,
        "overall_status": overall_status,
        "violations": violations,
        "compliance_pct": compliance_pct,
        "fields_passed": fields_passed,
        "fields_total": fields_total,
    }