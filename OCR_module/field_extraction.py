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

    # Check whether MRP mentions inclusive of taxes

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

    # Split OCR text into individual cleaned lines
    lines = [
        line.strip()
        for line in raw_text.splitlines()
        if line.strip()
    ]

    net_labels = (
        "net quantity",
        "net qty",
        "net wt",
        "net weight",
        "net feight",
    )

    quantity_pattern = re.compile(
        r"^\s*(\d+(?:\.\d+)?)\s*"
        r"(g|gm|gms|gram|grams|kg|kgs|ml|"
        r"l|ltr|litre|litres|liter|liters)\s*$",
        re.IGNORECASE,
    )

    # First look for "Net Quantity" and then check
    # the same line and the next few OCR lines.
    for index, line in enumerate(lines):

        normalized_line = re.sub(
            r"\s+",
            " ",
            line.lower()
        ).strip()

        if any(label in normalized_line for label in net_labels):

            # Check the current line + next 3 lines
            candidate_lines = lines[index:index + 4]

            for candidate in candidate_lines:

                qty_match = quantity_pattern.search(
                    candidate
                )

                if qty_match:

                    number = qty_match.group(1)
                    unit = qty_match.group(2)

                    fields["net_quantity"]["detected"] = True

                    fields["net_quantity"]["value"] = (
                        f"{number} {unit}"
                    )

                    break

        if fields["net_quantity"]["detected"]:
            break

    # ----------------------------------------------------------
    # Fallback: look for any standalone quantity
    # ----------------------------------------------------------

    if not fields["net_quantity"]["detected"]:

        for line in lines:

            qty_match = quantity_pattern.search(line)

            if qty_match:

                number = qty_match.group(1)
                unit = qty_match.group(2)

                fields["net_quantity"]["detected"] = True

                fields["net_quantity"]["value"] = (
                    f"{number} {unit}"
                )

                break
    # ----------------------------------------------------------
    # Generic quantity fallback
    # ----------------------------------------------------------

    if not fields["net_quantity"]["detected"]:

        generic_qty_matches = re.findall(
            r"\b"
            r"(\d+(?:\.\d+)?)"
            r"\s*"
            r"(gms?|grams?|kgs?|kg|ml|litres?|liters?|ltr|l)"
            r"\b",
            raw_text,
            re.IGNORECASE,
        )

        if generic_qty_matches:

            number, unit = generic_qty_matches[0]

            fields["net_quantity"]["detected"] = True

            fields["net_quantity"]["value"] = (
                f"{number} {unit}"
            )

    # ==========================================================
    # MANUFACTURING / PACKING DATE
    # ==========================================================

    mfg_match = re.search(
        r"(D\.?O\.?P"
        r"|Date of (Mfg|Pack)"
        r"|DATE OF (MFG|PACK)"
        r"|D\.?e?\.?o?f?\s*Manufacture"
        r"|Month of Mfg"
        r"|Packed On"
        r"|Mfg"
        r"|Manufactured"
        r"|Packed"
        r"|PKD)"
        r"[\s\S]{0,40}?"
        r"("
        r"\d{1,2}\s*[\.\:\-\s]\s*[A-Za-z]{3,9}"
        r"[\.\:\-\s]?\s*\d{2,4}"
        r")",
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
            r"([A-Za-z]{3,9})"
            r"[\s\S]{0,20}?"
            r"(\d{4})",
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
                r"Packed On"
                r"\s*[:\-]?\s*"
                r"(\d{1,2}\s*/\s*\d{4})",
                raw_text,
                re.IGNORECASE,
            )

            if mfg_fallback3:

                fields["mfg_date"]["detected"] = True

                fields["mfg_date"]["value"] = clean_value(
                    mfg_fallback3.group(1)
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
        r"(?:"
        r"customer\s+care"
        r"|consumer\s+care"
        r"|toll[\s\-]*free"
        r"|helpline"
        r"|care\s+no"
        r"|customer\s+service"
        r")"
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
        r"("
        r"marketed by"
        r"|manufactured by"
        r"|manufacturers?\s*&?\s*distributed by"
        r"|packed by"
        r"|pkd by"
        r"|mfd,?\s*pkd\s*&?\s*mktd by"
        r"|mfd by"
        r"|mktd by"
        r")"
        r"[\s:]*"
        r"([^\n]+(\n[^\n]+){0,2})",
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
            r"("
            r"[A-Z][A-Za-z\s]{2,30}"
            r"("
            r"Industries"
            r"|Bakery"
            r"|Foods"
            r"|Enterprises"
            r"|Traders"
            r"|Sweets"
            r"|& Co\.?"
            r"|Pvt\.?\s*Ltd\.?"
            r")"
            r")"
            r"[\s\S]{0,60}?"
            r"("
            r"[A-Z][a-z]+,?\s*"
            r"("
            r"Mangalore"
            r"|Bangalore"
            r"|Mysore"
            r"|Mumbai"
            r"|Delhi"
            r"|Chennai"
            r"|Pune"
            r"|Bengaluru"
            r"|[A-Z][a-z]+"
            r")"
            r")",
            raw_text,
            re.IGNORECASE,
        )

        if addr_fallback:

            fields["manufacturer_address"]["detected"] = True

            fields["manufacturer_address"]["value"] = clean_value(
                addr_fallback.group()
            )

    return fields