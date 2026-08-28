"""
Legal Metrology Rule Engine
Evaluates normalized OCR-extracted packaging fields
against compliance rules.

The OCR module uses:
    net_quantity
    manufacturer_address

The backend normalizes these to:
    net_qty
    address

The rule engine therefore uses the normalized backend names.
"""

import math


# --------------------------------------------------
# Field groups
# --------------------------------------------------

CRITICAL_FIELDS = [
    "mrp",
    "net_qty",
    "consumer_care",
]

SUPPORTING_FIELDS = [
    "mfg_date",
    "address",
    "best_before_date",
]

POINTS_PER_SUPPORTING_FIELD = 10


# --------------------------------------------------
# Display metadata
# --------------------------------------------------

FIELD_META = {
    "mrp": {
        "label": "Max Retail Price (MRP)",
        "tier": "critical",
        "rule": "Rule 6(1)(e)",
    },

    "net_qty": {
        "label": "Net Quantity",
        "tier": "critical",
        "rule": "Rule 6(1)(b)",
    },

    "consumer_care": {
        "label": "Consumer Care Details",
        "tier": "critical",
        "rule": "Rule 6(1)(h)",
    },

    "mfg_date": {
        "label": "Month & Year of Packing",
        "tier": "supporting",
        "rule": "Rule 6(1)(d)",
    },

    "address": {
        "label": "Manufacturer Address",
        "tier": "supporting",
        "rule": "Rule 6(1)(a)",
    },

    "best_before_date": {
        "label": "Best Before Date",
        "tier": "supporting",
        "rule": "FSSAI labeling (not LMPC) — verify",
    },

    "font_readability": {
        "label": "Minimum Font Size (MRP / Net Qty)",
        "tier": "info",
        "rule": "Rule 7(1)",
    },
}


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _as_dict(payload):
    """
    Accept either:
    - a normal dict
    - a Pydantic model such as ScanInput
    """
    if payload is None:
        return {}

    if hasattr(payload, "dict"):
        return payload.dict()

    return payload


def _field_status(field_data):
    """
    Returns:
        detected, value
    """
    if not isinstance(field_data, dict):
        return False, None

    return (
        bool(field_data.get("detected")),
        field_data.get("value"),
    )


# --------------------------------------------------
# Rule Engine
# --------------------------------------------------

def run_rule_engine(extracted) -> dict:
    extracted = _as_dict(extracted)

    results = []

    critical_fail_fields = []

    supporting_score = 0
    supporting_pool = 0

    # ==================================================
    # CRITICAL FIELDS
    # ==================================================

    for key in CRITICAL_FIELDS:

        detected, value = _field_status(
            extracted.get(key)
        )

        status = (
            "pass"
            if detected
            else "fail"
        )

        if not detected:
            critical_fail_fields.append(key)

        results.append({
            "field": key,
            "label": FIELD_META[key]["label"],
            "tier": "critical",
            "rule": FIELD_META[key]["rule"],
            "status": status,
            "detected_value": (
                value
                if value
                else "Not detected"
            ),
        })

    # ==================================================
    # SUPPORTING FIELDS
    # ==================================================

    for key in SUPPORTING_FIELDS:

        field_data = extracted.get(key) or {}

        # Best Before can be marked not applicable
        if (
            key == "best_before_date"
            and field_data.get("applicable") is False
        ):
            results.append({
                "field": key,
                "label": FIELD_META[key]["label"],
                "tier": "supporting",
                "rule": FIELD_META[key]["rule"],
                "status": "not_applicable",
                "detected_value":
                    "N/A — not applicable to this product",
            })

            continue

        detected, value = _field_status(
            field_data
        )

        supporting_pool += (
            POINTS_PER_SUPPORTING_FIELD
        )

        if detected:
            supporting_score += (
                POINTS_PER_SUPPORTING_FIELD
            )

        results.append({
            "field": key,
            "label": FIELD_META[key]["label"],
            "tier": "supporting",
            "rule": FIELD_META[key]["rule"],
            "status": (
                "pass"
                if detected
                else "fail"
            ),
            "detected_value": (
                value
                if value
                else "Not detected"
            ),
        })

    # ==================================================
    # READABILITY
    # ==================================================

    readability_notes = []

    for key in (
        "mrp",
        "net_qty",
    ):
        field_data = (
            extracted.get(key) or {}
        )

        flag = field_data.get(
            "small_text_flag"
        )

        pct = field_data.get(
            "text_height_pct"
        )

        if flag is None or pct is None:
            continue

        readability_notes.append({
            "field": key,
            "label": FIELD_META[key]["label"],
            "text_height_pct": pct,
            "small_text_flag": flag,
        })

    # ==================================================
    # Overall supporting score
    # ==================================================

    supporting_threshold = (
        math.ceil(
            supporting_pool * 2 / 3
        )
        if supporting_pool
        else 0
    )

    supporting_pass = (
        supporting_score
        >= supporting_threshold
    )

    # ==================================================
    # Overall compliance
    # ==================================================

    is_critical_fail = (
        len(critical_fail_fields) > 0
    )

    overall_status = (
        "compliant"
        if (
            not is_critical_fail
            and supporting_pass
        )
        else "non-compliant"
    )

    # ==================================================
    # Violations
    # ==================================================

    violations = []

    for result in results:

        if result["status"] == "fail":

            violations.append({
                "rule": result["rule"],
                "description":
                    f"Missing or undetected: "
                    f"{result['label']}",
            })

    for note in readability_notes:

        if note["small_text_flag"]:

            violations.append({
                "rule":
                    FIELD_META["font_readability"]["rule"],

                "description":
                    f"{note['label']} text below "
                    f"readable size threshold "
                    f"({note['text_height_pct']:.1f}% "
                    f"of image height)",
            })

    # ==================================================
    # Compliance percentage
    # ==================================================

    critical_passed = (
        len(CRITICAL_FIELDS)
        - len(critical_fail_fields)
    )

    supporting_passed = (
        supporting_score
        // POINTS_PER_SUPPORTING_FIELD
        if POINTS_PER_SUPPORTING_FIELD
        else 0
    )

    fields_total = (
        len(CRITICAL_FIELDS)
        + (
            supporting_pool
            // POINTS_PER_SUPPORTING_FIELD
        )
    )

    fields_passed = (
        critical_passed
        + supporting_passed
    )

    compliance_pct = (
        round(
            fields_passed
            / fields_total
            * 100
        )
        if fields_total
        else 0
    )

    # ==================================================
    # Final response
    # ==================================================

    return {
        "field_results": results,
        "readability_notes": readability_notes,
        "critical_fail_fields":
            critical_fail_fields,
        "supporting_score":
            supporting_score,
        "supporting_pool":
            supporting_pool,
        "supporting_threshold":
            supporting_threshold,
        "overall_status":
            overall_status,
        "violations":
            violations,
        "compliance_pct":
            compliance_pct,
        "fields_passed":
            fields_passed,
        "fields_total":
            fields_total,
    }