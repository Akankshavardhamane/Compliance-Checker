import re


def clean_value(text):
    return re.sub(r"\s+", " ", text).strip()


def classify_fields(raw_text):
    fields = {
        "mrp": {
            "detected": False,
            "value": None,
            "says_inclusive_of_taxes": False,
        },
        "net_quantity": {
            "detected": False,
            "value": None,
        },
        "mfg_date": {
            "detected": False,
            "value": None,
        },
        "consumer_care": {
            "detected": False,
            "value": None,
        },
        "manufacturer_address": {
            "detected": False,
            "value": None,
        },
        "best_before_date": {
            "detected": False,
            "value": None,
            "applicable": True,
        },
    }

    # ==========================================================
    # MRP
    # ==========================================================
    #
    # Handles examples such as:
    #   MRP RS
    #   40.00
    #
    #   MRP: ₹40
    #
    #   Max, Retail Price:
    #   60.00
    #
    #   Max Retail Price: Rs 60
    #
    #   Maximum Retail Price ₹60
    #
    mrp_match = re.search(
        r"(?:"
        r"M\s*\.?\s*R\s*\.?\s*P"
        r"|"
        r"Max(?:imum)?\s*[,.:;\-]?\s*Retail\s*[,.:;\-]?\s*Price"
        r"|"
        r"Retail\s*Price"
        r")"
        r"\s*[:\-]?\s*"
        r"(?:Rs\.?|₹|Rupees)?"
        r"\s*"
        r"(\d{1,6}(?:[.,]\d{1,2})?)",
        raw_text,
        re.IGNORECASE,
    )

    if mrp_match:
        fields["mrp"]["detected"] = True
        fields["mrp"]["value"] = (
            clean_value(mrp_match.group(1)) + "/-"
        )
    else:
        # Currency fallback
        mrp_match = re.search(
            r"(?:Rs\.?|₹|Rupees)"
            r"\s*"
            r"(\d{1,6}(?:[.,]\d{1,2})?)",
            raw_text,
            re.IGNORECASE,
        )

        if mrp_match:
            fields["mrp"]["detected"] = True
            fields["mrp"]["value"] = clean_value(
                mrp_match.group(0)
            )

    if fields["mrp"]["detected"]:
        fields["mrp"]["says_inclusive_of_taxes"] = bool(
            re.search(
                r"(?:incl?|inclusive|included)"
                r"\.?\s*(?:of)?\s*(?:all\s+)?tax(?:es)?",
                raw_text,
                re.IGNORECASE,
            )
        )

    # ==========================================================
    # NET QUANTITY
    # ==========================================================
    #
    # Handles:
    #   NET WT
    #   100GMS
    #
    #   Net Quantity: 150 gms
    #
    #   NET WEIGHT
    #   150 g
    #
    quantity_value_pattern = (
        r"(\d+(?:\.\d+)?)\s*"
        r"(gms?|grams?|kg|kgs|ml|litres?|l)\b"
    )

    qty_match = re.search(
        r"(?:Net\s+Quantity|Net\s+Wt|Net\s+Weight|Net\s+Feight)"
        r"\s*[:\-]?\s*"
        + quantity_value_pattern,
        raw_text,
        re.IGNORECASE,
    )

    if qty_match:
        fields["net_quantity"]["detected"] = True
        fields["net_quantity"]["value"] = clean_value(
            qty_match.group(0)
        )

    if not fields["net_quantity"]["detected"]:
        qty_match = re.search(
            r"(?:Net\s+Quantity|Net\s+Wt|Net\s+Weight|Net\s+Feight)"
            r"[\s\S]{0,30}?"
            + quantity_value_pattern,
            raw_text,
            re.IGNORECASE,
        )

        if qty_match:
            fields["net_quantity"]["detected"] = True
            fields["net_quantity"]["value"] = clean_value(
                qty_match.group(0)
            )

    # Generic quantity fallback
    if not fields["net_quantity"]["detected"]:
        generic_qty = re.search(
            r"\b\d+(?:\.\d+)?\s*"
            r"(?:gms?|grams?|kg|kgs|ml|litres?|l)\b",
            raw_text,
            re.IGNORECASE,
        )

        if generic_qty:
            fields["net_quantity"]["detected"] = True
            fields["net_quantity"]["value"] = clean_value(
                generic_qty.group(0)
            )

    # ==========================================================
    # MANUFACTURING / PACKING DATE
    # ==========================================================
    mfg_match = re.search(
        r"(D\.?O\.?P|Date of (Mfg|Pack)|.ATE OF (MFG|PACK)|"
        r"D\.?e?\.?o?f?\s*Manufacture|Month of Mfg|Packed On|Mfg|"
        r"Manufactured|Packed|PKD)"
        r"[\s\S]{0,40}?"
        r"(\d{1,2}\s*[\.\:\-\s]\s*[A-Za-z]{3,9}"
        r"[\.\:\-\s]?\s*\d{2,4})",
        raw_text,
        re.IGNORECASE,
    )

    if mfg_match:
        fields["mfg_date"]["detected"] = True
        fields["mfg_date"]["value"] = clean_value(
            mfg_match.group(mfg_match.lastindex)
        )
    else:
        mfg_fallback2 = re.search(
            r"Month of Mfg\.?[\s\S]{0,20}?"
            r"([A-Za-z]{3,9})[\s\S]{0,20}?(\d{4})",
            raw_text,
            re.IGNORECASE,
        )

        if mfg_fallback2:
            fields["mfg_date"]["detected"] = True
            fields["mfg_date"]["value"] = clean_value(
                mfg_fallback2.group(1)
                + " "
                + mfg_fallback2.group(2)
            )
        else:
            mfg_fallback3 = re.search(
                r"Packed On\s*[:\-]?\s*"
                r"(\d{1,2}\s*/\s*\d{4})",
                raw_text,
                re.IGNORECASE,
            )

            if mfg_fallback3:
                fields["mfg_date"]["detected"] = True
                fields["mfg_date"]["value"] = clean_value(
                    mfg_fallback3.group()
                )

    # ==========================================================
    # BEST BEFORE
    # ==========================================================
    bb_match = re.search(
        r"Best\s*Before"
        r"\s*[:\-]?\s*"
        r"("
        r"\d{1,2}\s*[\.\-\s]?\s*[A-Za-z]{3,9}"
        r"(?:[\.\-\s]?\s*\d{2,4})?"
        r"|"
        r"\d+\s*days?\s*from\s*packing"
        r"|"
        r"\d+\s*months?\s*from\s*packing"
        r"|"
        r"\d+\s*months?"
        r")",
        raw_text,
        re.IGNORECASE,
    )

    if bb_match:
        fields["best_before_date"]["detected"] = True
        fields["best_before_date"]["value"] = clean_value(
            bb_match.group()
        )

    # ==========================================================
    # CONSUMER CARE
    # ==========================================================
    consumer_label_pattern = (
        r"(?:customer\s+care|consumer\s+care|"
        r"toll[\s\-]*free|"
        r"helpline|"
        r"care\s+no|"
        r"customer\s+service)"
    )

    phone_pattern = (
        r"(?:"
        r"\d{10}"
        r"|"
        r"\d{4}[\s\-]\d{3}[\s\-]\d{3}"
        r"|"
        r"\d{4}[\s\-]\d{3}[\s\-]\d{4}"
        r")"
    )

    email_pattern = r"[\w.\-+]+@[\w.\-]+\.[A-Za-z]{2,}"

    # Labelled customer-care phone
    care_match = re.search(
        consumer_label_pattern
        + r"[\s:.\-#]*"
        + r"(?:No\.?|Number)?"
        + r"[\s:.\-#]*"
        + r"("
        + phone_pattern
        + r")",
        raw_text,
        re.IGNORECASE,
    )

    # Labelled customer-care email
    if not care_match:
        care_match = re.search(
            consumer_label_pattern
            + r"[\s:.\-#]*"
            + r"("
            + email_pattern
            + r")",
            raw_text,
            re.IGNORECASE,
        )

    # Explicit Mobile / Phone / Contact
    if not care_match:
        care_match = re.search(
            r"(?:Mobile|Phone|Contact)"
            r"[\s:.\-#]*"
            r"("
            + phone_pattern
            + r")",
            raw_text,
            re.IGNORECASE,
        )

    if care_match:
        fields["consumer_care"]["detected"] = True
        fields["consumer_care"]["value"] = clean_value(
            care_match.group()
        )

    # ==========================================================
    # MANUFACTURER ADDRESS
    # ==========================================================
    addr_match = re.search(
        r"(marketed by|manufactured by|manufacturers?\s*&?\s*"
        r"distributed by|packed by|pkd by|"
        r"mfd,?\s*pkd\s*&?\s*mktd by|mfd by|mktd by)"
        r"[\s:]*([^\n]+(\n[^\n]+){0,2})",
        raw_text,
        re.IGNORECASE,
    )

    if addr_match:
        fields["manufacturer_address"]["detected"] = True
        fields["manufacturer_address"]["value"] = clean_value(
            addr_match.group()
        )
    else:
        addr_fallback = re.search(
            r"([A-Z][A-Za-z\s]{2,30}"
            r"(Industries|Bakery|Foods|Enterprises|Traders|"
            r"Sweets|& Co\.?|Pvt\.?\s*Ltd\.?))"
            r"[\s\S]{0,60}?"
            r"([A-Z][a-z]+,?\s*"
            r"(Mangalore|Bangalore|Mysore|Mumbai|Delhi|Chennai|"
            r"Pune|Bengaluru|[A-Z][a-z]+))",
            raw_text,
            re.IGNORECASE,
        )

        if addr_fallback:
            fields["manufacturer_address"]["detected"] = True
            fields["manufacturer_address"]["value"] = clean_value(
                addr_fallback.group()
            )

    return fields