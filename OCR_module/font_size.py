import re
from PIL import Image

def get_image_height(image_path):
    with Image.open(image_path) as img:
        return img.height

def get_line_heights(overlay_data, image_path):
    img_height = get_image_height(image_path)
    lines = overlay_data.get('TextOverlay', {}).get('Lines', [])
    results = []
    for line in lines:
        height_px = line.get('MaxHeight', 0)
        results.append({
            "text": line['LineText'],
            "height_px": height_px,
            "top_px": line.get('MinTop', 0),
            "height_pct": round((height_px / img_height) * 100, 2)
        })
    return results

def get_field_font_heights(fields, line_heights, threshold_pct=3.0):
    """
    threshold_pct is a PROVISIONAL heuristic value based on limited testing.
    text_height_pct is a RELATIVE measure (% of image height) — not a real
    mm measurement, since photos have no fixed scale without a calibration
    reference object in frame.
    """
    for field_name, field_data in fields.items():
        if not isinstance(field_data, dict) or not field_data.get("detected"):
            field_data["text_height_pct"] = None
            field_data["small_text_flag"] = None
            continue

        value = field_data.get("value")
        fragment = re.sub(r'[^A-Za-z0-9]', '', value or "")[:6]

        match_line = None
        if fragment:
            for line in line_heights:
                line_fragment = re.sub(r'[^A-Za-z0-9]', '', line['text'])
                if fragment in line_fragment:
                    match_line = line
                    break

        field_data["text_height_pct"] = match_line["height_pct"] if match_line else None
        field_data["small_text_flag"] = (
            match_line["height_pct"] < threshold_pct if match_line else None
        )

    return fields