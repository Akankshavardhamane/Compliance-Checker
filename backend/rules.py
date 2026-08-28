import re

def check_mrp(field):
    if not field.detected or not field.value:
        return {"field": "mrp", "label": "MRP", "status": "fail",
                "detected_value": None, "reason": "MRP not detected on label"}
    value = field.value.lower()
    if "incl" not in value and "inclusive" not in value:
        return {"field": "mrp", "label": "MRP", "status": "fail",
                "detected_value": field.value,
                "reason": "MRP must state 'inclusive of all taxes'"}
    return {"field": "mrp", "label": "MRP", "status": "pass",
            "detected_value": field.value, "reason": ""}


def check_net_qty(field):
    if not field.detected or not field.value:
        return {"field": "net_qty", "label": "Net Quantity", "status": "fail",
                "detected_value": None, "reason": "Net quantity not detected on label"}
    if not re.search(r'\d+\s*(g|kg|ml|l|gm|litre|litres)\b', field.value.lower()):
        return {"field": "net_qty", "label": "Net Quantity", "status": "fail",
                "detected_value": field.value,
                "reason": "Net quantity not in a standard unit (g/kg/ml/l)"}
    return {"field": "net_qty", "label": "Net Quantity", "status": "pass",
            "detected_value": field.value, "reason": ""}


def check_mfg_date(field):
    if not field.detected or not field.value:
        return {"field": "mfg_date", "label": "Manufacturing Date", "status": "fail",
                "detected_value": None, "reason": "Manufacturing date not detected on label"}
    if not re.search(r'\d{1,2}[/-]\d{4}|\d{4}', field.value):
        return {"field": "mfg_date", "label": "Manufacturing Date", "status": "fail",
                "detected_value": field.value,
                "reason": "Manufacturing date not in a valid month/year format"}
    return {"field": "mfg_date", "label": "Manufacturing Date", "status": "pass",
            "detected_value": field.value, "reason": ""}


def check_address(field):
    if not field.detected or not field.value:
        return {"field": "address", "label": "Manufacturer Address", "status": "fail",
                "detected_value": None, "reason": "Manufacturer address not detected on label"}
    if not re.search(r'\b\d{6}\b', field.value):
        return {"field": "address", "label": "Manufacturer Address", "status": "fail",
                "detected_value": field.value,
                "reason": "Address missing a valid 6-digit PIN code"}
    return {"field": "address", "label": "Manufacturer Address", "status": "pass",
            "detected_value": field.value, "reason": ""}


def check_consumer_care(field):
    if not field.detected or not field.value:
        return {"field": "consumer_care", "label": "Consumer Care", "status": "fail",
                "detected_value": None, "reason": "Consumer care details not detected on label"}
    has_phone = re.search(r'(\+?\d[\d\-\s]{7,}\d)', field.value)
    has_email = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', field.value)
    if not (has_phone or has_email):
        return {"field": "consumer_care", "label": "Consumer Care", "status": "fail",
                "detected_value": field.value,
                "reason": "No valid phone number or email found"}
    if field.font_size_ok is False:
        return {"field": "consumer_care", "label": "Consumer Care", "status": "fail",
                "detected_value": field.value,
                "reason": "Font size below minimum readability requirement"}
    return {"field": "consumer_care", "label": "Consumer Care", "status": "pass",
            "detected_value": field.value, "reason": ""}


def check_country_of_origin(field, is_imported):
    if not is_imported:
        return None
    if not field or not field.detected or not field.value:
        return {"field": "country_of_origin", "label": "Country of Origin", "status": "fail",
                "detected_value": None,
                "reason": "Country of origin required for imported products but not detected"}
    return {"field": "country_of_origin", "label": "Country of Origin", "status": "pass",
            "detected_value": field.value, "reason": ""}


EXEMPT_TYPES = {"free_sample", "bulk_institutional", "export_only"}

def run_rule_engine(scan_input):
    if scan_input.exemption in EXEMPT_TYPES:
        return {
            "overall_status": "exempt",
            "compliance_pct": 100.0,
            "fields_passed": 0,
            "fields_total": 0,
            "field_results": []
        }

    results = []
    results.append(check_mrp(scan_input.mrp))
    results.append(check_net_qty(scan_input.net_qty))
    results.append(check_mfg_date(scan_input.mfg_date))
    results.append(check_address(scan_input.address))
    results.append(check_consumer_care(scan_input.consumer_care))

    coo_result = check_country_of_origin(scan_input.country_of_origin, scan_input.is_imported)
    if coo_result:
        results.append(coo_result)

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "pass")
    compliance_pct = round((passed / total) * 100, 1) if total > 0 else 0.0
    overall_status = "compliant" if passed == total else "non-compliant"

    return {
        "overall_status": overall_status,
        "compliance_pct": compliance_pct,
        "fields_passed": passed,
        "fields_total": total,
        "field_results": results
    }