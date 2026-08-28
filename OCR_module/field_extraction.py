import re

def clean_value(text):
    return re.sub(r'\s+', ' ', text).strip()

def classify_fields(raw_text):
    fields = {
        "mrp": {"detected": False, "value": None, "says_inclusive_of_taxes": False},
        "net_quantity": {"detected": False, "value": None},
        "mfg_date": {"detected": False, "value": None},
        "consumer_care": {"detected": False, "value": None},
        "manufacturer_address": {"detected": False, "value": None},
        "best_before_date": {"detected": False, "value": None, "applicable": True},
    }

    # --- MRP ---
    mrp_match = re.search(r'(Retail Price|M\.?R\.?P)[\s\S]{0,15}?(\d+)\s*/-?', raw_text, re.IGNORECASE)
    if mrp_match:
        fields["mrp"]["detected"] = True
        fields["mrp"]["value"] = clean_value(mrp_match.group(2)) + "/-"
    else:
        mrp_match = re.search(r'\bRs\.?\s*[\d,]+\.?\d*|\₹\s*[\d,]+\.?\d*', raw_text, re.IGNORECASE)
        if not mrp_match:
            mrp_match = re.search(r'(Retail Price|M\.?R\.?P)[^\d]{0,25}?(\d+\.?\d*)', raw_text, re.IGNORECASE)
        if mrp_match:
            fields["mrp"]["detected"] = True
            fields["mrp"]["value"] = clean_value(mrp_match.group())

    if fields["mrp"]["detected"]:
        # FIX: now catches "Incl." (abbreviated) as well as "Inclusive"/"Inclusives"
        fields["mrp"]["says_inclusive_of_taxes"] = bool(
            re.search(r'(in)?clu?\w*\.?\s+of\s+(all\s+)?tax\w*', raw_text, re.IGNORECASE)
        )

    # --- Net Quantity ---
    qty_match = re.search(
        r'(Net Quantity|Net Wt|Net Weight|Net Feight)[^\d]{0,15}(\d+(\.\d+)?\s*(g|gm|gms|kg|ml|l|litre|gram)\b)',
        raw_text, re.IGNORECASE
    )
    if not qty_match:
        qty_match = re.search(r'\d+(\.\d+)?\s*(gms|gm|g|kg|ml|l|litre|gram)\b', raw_text, re.IGNORECASE)
    if qty_match:
        fields["net_quantity"]["detected"] = True
        fields["net_quantity"]["value"] = clean_value(qty_match.group())

    if not fields["net_quantity"]["detected"]:
        qty_fallback = re.search(
            r'(Net Quantity|Net Wt|Net Weight|Net Feight)[^\d]{0,10}(\d[\d\s]{0,3}\d|\d)',
            raw_text, re.IGNORECASE
        )
        if qty_fallback:
            fields["net_quantity"]["detected"] = True
            fields["net_quantity"]["value"] = clean_value(qty_fallback.group(2)).replace(' ', '') + " (unit not confirmed by OCR)"

    # --- Mfg/Packing date ---
    mfg_match = re.search(
        r'(D\.?O\.?P|Date of (Mfg|Pack)|.ATE OF (MFG|PACK)|D\.?e?\.?o?f?\s*Manufacture|Month of Mfg|Packed On|Mfg|Manufactured|Packed|PKD)'
        r'[\s\S]{0,40}?(\d{1,2}\s*[\.\:\-\s]\s*[A-Za-z]{3,9}[\.\:\-\s]?\s*\d{2,4})',
        raw_text, re.IGNORECASE
    )
    if mfg_match:
        fields["mfg_date"]["detected"] = True
        fields["mfg_date"]["value"] = clean_value(mfg_match.group(mfg_match.lastindex))
    else:
        mfg_fallback2 = re.search(
            r'Month of Mfg\.?[\s\S]{0,20}?([A-Za-z]{3,9})[\s\S]{0,20}?(\d{4})',
            raw_text, re.IGNORECASE
        )
        if mfg_fallback2:
            fields["mfg_date"]["detected"] = True
            fields["mfg_date"]["value"] = clean_value(mfg_fallback2.group(1) + " " + mfg_fallback2.group(2))
        else:
            # NEW fallback: "Packed On : 08/2026" style (numeric month/year, no day, no month-name)
            mfg_fallback3 = re.search(
                r'Packed On\s*[:\-]?\s*(\d{1,2}\s*/\s*\d{4})',
                raw_text, re.IGNORECASE
            )
            if mfg_fallback3:
                fields["mfg_date"]["detected"] = True
                fields["mfg_date"]["value"] = clean_value(mfg_fallback3.group())

    # --- Best Before ---
    bb_match = re.search(
        r'Best Before\.?\s*[:\-]?\s*(\d{1,2}\s*[\.\-\s]?\s*\w+[\.\-\s]?\s*\d{2,4}|\d+\s*days?\s*from\s*\w+|\d+\s*months?\s*from\s*[\w\s]*|\d+\s*months?)',
        raw_text, re.IGNORECASE
    )
    if bb_match:
        fields["best_before_date"]["detected"] = True
        fields["best_before_date"]["value"] = clean_value(bb_match.group())

    # --- Consumer care ---
    care_match = re.search(
        r'(customer care|consumer care|toll.?free)[^\d@]{0,15}'
        r'(\d{10}(,\s*\d{10})?|\d{4}[-\s]\d{3}[-\s]\d{4}|[\w.\-]+@[\w.\-]+)',
        raw_text, re.IGNORECASE
    )
    if not care_match:
        care_match = re.search(r'(Mobile|Phone)[\s:]*[\d\s\-]*?(\d{10})', raw_text, re.IGNORECASE)
    if not care_match:
        care_match = re.search(r'\b\d{10}\b|[\w.\-]+@[\w.\-]+', raw_text)
    if care_match:
        fields["consumer_care"]["detected"] = True
        fields["consumer_care"]["value"] = clean_value(care_match.group())

    # --- Manufacturer address ---
    addr_match = re.search(
        r'(marketed by|manufactured by|manufacturers?\s*&?\s*distributed by|packed by|pkd by|'
        r'mfd,?\s*pkd\s*&?\s*mktd by|mfd by|mktd by)'
        r'[\s:]*([^\n]+(\n[^\n]+){0,2})',
        raw_text, re.IGNORECASE
    )
    if addr_match:
        fields["manufacturer_address"]["detected"] = True
        fields["manufacturer_address"]["value"] = clean_value(addr_match.group())
    else:
        addr_fallback = re.search(
            r'([A-Z][A-Za-z\s]{2,30}'
            r'(Industries|Bakery|Foods|Enterprises|Traders|Sweets|& Co\.?|Pvt\.?\s*Ltd\.?))'
            r'[\s\S]{0,60}?([A-Z][a-z]+,?\s*(Mangalore|Bangalore|Mysore|Mumbai|Delhi|Chennai|Pune|Bengaluru|[A-Z][a-z]+))',
            raw_text, re.IGNORECASE
        )
        if addr_fallback:
            fields["manufacturer_address"]["detected"] = True
            fields["manufacturer_address"]["value"] = clean_value(addr_fallback.group())

    return fields