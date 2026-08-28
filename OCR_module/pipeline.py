from ocr import get_ocr_text
from field_extraction import classify_fields
from font_size import get_line_heights, get_field_font_heights
import json

def process_label(image_path):
    parsed = get_ocr_text(image_path, return_overlay=True)
    raw_text = parsed['ParsedText']

    fields = classify_fields(raw_text)

    line_heights = get_line_heights(parsed, image_path)
    fields = get_field_font_heights(fields, line_heights)

    return fields

if __name__ == "__main__":
    result = process_label('testimage3.jpeg')
    print(json.dumps(result, indent=2))