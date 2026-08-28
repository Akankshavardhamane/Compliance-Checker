from ocr import get_ocr_text
from font_size import get_line_heights, flag_small_text
import json

parsed = get_ocr_text('test_img.jpeg', return_overlay=True)
line_heights = get_line_heights(parsed, 'test_img.jpeg')

for l in line_heights:
    print(f"{l['height_pct']:>6}%  |  {l['text']}")