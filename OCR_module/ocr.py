import os
import requests

API_KEY = os.environ.get('OCRSPACE_API_KEY')
if not API_KEY:
    raise Exception("Missing OCRSPACE_API_KEY environment variable. Set it before running.")

DEBUG = False 

def get_ocr_text(image_path, return_overlay=False):
    with open(image_path, 'rb') as f:
        response = requests.post(
            'https://api.ocr.space/parse/image',
            files={'file': f},
            data={
                'apikey': API_KEY,
                'language': 'eng',
                'OCREngine': 2,
                'isOverlayRequired': True,
            }
        )
    result = response.json()

    if DEBUG:
        print("DEBUG - Full raw response:", result)

    if result.get('IsErroredOnProcessing') or 'ParsedResults' not in result:
        raise Exception(result.get('ErrorMessage') or result.get('error', 'Unknown OCR error'))

    if return_overlay:
        return result['ParsedResults'][0]

    return result['ParsedResults'][0]['ParsedText']