import re
from PIL import Image


def get_image_height(image_path):
    with Image.open(image_path) as img:
        return img.height


def get_line_heights(overlay_data, image_path):
    img_height = get_image_height(image_path)

    lines = (
        overlay_data
        .get("TextOverlay", {})
        .get("Lines", [])
    )

    results = []

    for line in lines:
        height_px = line.get("MaxHeight", 0)

        results.append(
            {
                "text": line.get("LineText", ""),
                "height_px": height_px,
                "top_px": line.get("MinTop", 0),
                "height_pct": round(
                    (height_px / img_height) * 100,
                    2,
                )
                if img_height > 0
                else 0,
            }
        )

    return results


def get_field_font_heights(
    fields,
    line_heights,
    threshold_pct=3.0,
):
    """
    Adds font-size information to each detected field.

    threshold_pct is a provisional heuristic based on
    the percentage of text height relative to image height.
    """

    for field_name, field_data in fields.items():

        # Skip anything that is not a field dictionary
        if not isinstance(field_data, dict):
            continue

        # --------------------------------------------------
        # Field not detected
        # --------------------------------------------------

        if not field_data.get("detected"):

            field_data["text_height_pct"] = None
            field_data["small_text_flag"] = None

            continue

        # --------------------------------------------------
        # Get extracted value
        # --------------------------------------------------

        value = field_data.get("value")

        if not value:

            field_data["text_height_pct"] = None
            field_data["small_text_flag"] = None

            continue

        # --------------------------------------------------
        # Normalize value for comparison
        # --------------------------------------------------

        fragment = re.sub(
            r"[^A-Za-z0-9]",
            "",
            str(value),
        )[:6]

        match_line = None

        # --------------------------------------------------
        # Find OCR line containing the extracted value
        # --------------------------------------------------

        if fragment:

            for line in line_heights:

                line_text = line.get(
                    "text",
                    "",
                )

                line_fragment = re.sub(
                    r"[^A-Za-z0-9]",
                    "",
                    line_text,
                )

                if fragment.lower() in line_fragment.lower():

                    match_line = line
                    break

        # --------------------------------------------------
        # Add font information
        # --------------------------------------------------

        if match_line:

            field_data["text_height_pct"] = (
                match_line["height_pct"]
            )

            field_data["small_text_flag"] = (
                match_line["height_pct"]
                < threshold_pct
            )

        else:

            field_data["text_height_pct"] = None
            field_data["small_text_flag"] = None

    return fields