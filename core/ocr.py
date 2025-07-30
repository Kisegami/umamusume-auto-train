import pytesseract
from PIL import Image
import numpy as np
import os

# Configure Tesseract to use the custom trained data
tesseract_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Tesseract-OCR')
tessdata_dir = os.path.join(tesseract_dir, 'tessdata')

if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = os.path.join(tesseract_dir, 'tesseract.exe')

os.environ['TESSDATA_PREFIX'] = tessdata_dir

def extract_text(pil_img: Image.Image) -> str:
    """Extract text from image using Tesseract OCR"""
    try:
        # Convert PIL image to numpy array if needed
        if isinstance(pil_img, Image.Image):
            img_np = np.array(pil_img)
        else:
            img_np = pil_img
            
        # Use Tesseract with custom configuration for better accuracy
        config = '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789%().- '
        text = pytesseract.image_to_string(img_np, config=config, lang='eng')
        return text.strip()
    except Exception as e:
        print(f"[WARNING] OCR extraction failed: {e}")
        return ""

def extract_number(pil_img: Image.Image) -> str:
    """Extract numbers from image using Tesseract OCR"""
    try:
        # Convert PIL image to numpy array if needed
        if isinstance(pil_img, Image.Image):
            img_np = np.array(pil_img)
        else:
            img_np = pil_img
            
        # Use Tesseract with configuration optimized for numbers
        config = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789 '
        text = pytesseract.image_to_string(img_np, config=config, lang='eng')
        return text.strip()
    except Exception as e:
        print(f"[WARNING] Number extraction failed: {e}")
        return ""

def extract_turn_number(pil_img: Image.Image) -> str:
    """Extract turn numbers with specialized configuration for better digit recognition"""
    try:
        # Convert PIL image to numpy array if needed
        if isinstance(pil_img, Image.Image):
            img_np = np.array(pil_img)
        else:
            img_np = pil_img
            
        # Try multiple PSM modes for better digit recognition
        configs = [
            '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789',  # Single word
            '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789',  # Single line
            '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789',  # Uniform block
        ]
        
        for config in configs:
            text = pytesseract.image_to_string(img_np, config=config, lang='eng')
            text = text.strip()
            if text and text.isdigit():
                return text
        
        # If no config worked, return the first non-empty result
        for config in configs:
            text = pytesseract.image_to_string(img_np, config=config, lang='eng')
            text = text.strip()
            if text:
                return text
                
        return ""
    except Exception as e:
        print(f"[WARNING] Turn number extraction failed: {e}")
        return ""

def extract_mood_text(pil_img: Image.Image) -> str:
    """Extract mood text with specialized configuration for better text recognition"""
    try:
        # Convert PIL image to numpy array if needed
        if isinstance(pil_img, Image.Image):
            img_np = np.array(pil_img)
        else:
            img_np = pil_img
            
        # Try multiple PSM modes for better text recognition
        configs = [
            '--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',  # Single word
            '--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',  # Single line
            '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',  # Uniform block
        ]
        
        for config in configs:
            text = pytesseract.image_to_string(img_np, config=config, lang='eng')
            text = text.strip()
            if text:
                return text
                
        return ""
    except Exception as e:
        print(f"[WARNING] Mood text extraction failed: {e}")
        return ""

def extract_failure_text(pil_img: Image.Image) -> str:
    """Extract failure rate text with specialized configuration"""
    try:
        # Convert PIL image to numpy array if needed
        if isinstance(pil_img, Image.Image):
            img_np = np.array(pil_img)
        else:
            img_np = pil_img
            
        # Try multiple PSM modes for better text recognition
        configs = [
            '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789%(). ',  # Uniform block
            '--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789%(). ',  # Single line
            '--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789%(). ',  # Single word
            '--oem 3 --psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789%(). ',  # Raw line
        ]
        
        for config in configs:
            text = pytesseract.image_to_string(img_np, config=config, lang='eng')
            text = text.strip()
            if text:
                return text
                
        return ""
    except Exception as e:
        print(f"[WARNING] Failure text extraction failed: {e}")
        return ""

def extract_failure_text_with_confidence(pil_img: Image.Image) -> tuple[str, float]:
    """Extract failure rate text with confidence score from Tesseract"""
    try:
        # Convert PIL image to numpy array if needed
        if isinstance(pil_img, Image.Image):
            img_np = np.array(pil_img)
        else:
            img_np = pil_img
            
        # Use Tesseract with data output to get confidence scores
        config = '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789%(). '
        ocr_data = pytesseract.image_to_data(img_np, config=config, lang='eng', output_type=pytesseract.Output.DICT)
        
        # Extract text and calculate average confidence
        text_parts = []
        confidences = []
        
        for i, text in enumerate(ocr_data['text']):
            if text.strip():  # Only consider non-empty text
                text_parts.append(text)
                confidences.append(ocr_data['conf'][i])
        
        if text_parts:
            full_text = ' '.join(text_parts).strip()
            avg_confidence = sum(confidences) / len(confidences) / 100.0  # Convert to 0-1 scale
            return full_text, avg_confidence
        else:
            return "", 0.0
            
    except Exception as e:
        print(f"[WARNING] Failure text extraction with confidence failed: {e}")
        return "", 0.0
