import pytesseract
from PIL import Image
import numpy as np
import cv2
import os
import json

# Configure Tesseract to use the custom trained data
tessdata_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tessdata')
os.environ['TESSDATA_PREFIX'] = tessdata_dir

# Load config and check debug mode
with open("config.json", "r", encoding="utf-8") as config_file:
    config = json.load(config_file)
    DEBUG_MODE = config.get("debug_mode", False)

def debug_print(message):
    """Print debug message only if DEBUG_MODE is enabled"""
    if DEBUG_MODE:
        print(message)

# Try to find tesseract executable automatically
try:
    # On Windows, try common installation paths
    if os.name == 'nt':
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME', ''))
        ]
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break
except Exception:
    pass  # Fall back to system PATH

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

def extract_event_name_text(pil_img: Image.Image) -> str:
    """Extract event name text from image using Tesseract OCR, trying multiple PSMs for best result."""
    try:
        if isinstance(pil_img, Image.Image):
            img_np = np.array(pil_img)
        else:
            img_np = pil_img

        # Apply preprocessing like event_ocr.py
        # Scale image 2x using high-quality interpolation
        height, width = img_np.shape[:2]
        new_width = int(width * 2.0)
        new_height = int(height * 2.0)
        scaled_img = cv2.resize(img_np, (new_width, new_height), 
                              interpolation=cv2.INTER_CUBIC)
        
        # Convert to grayscale if needed
        if len(scaled_img.shape) == 3:
            gray = cv2.cvtColor(scaled_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = scaled_img
        
        # Create binary image based on brightness threshold (200)
        # Invert so that dark text becomes black (0) and light background becomes white (255)
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        
        # Invert back to get black text on white background
        processed = cv2.bitwise_not(binary)
        
        # Use processed image for OCR
        img_np = processed

        configs = [
            '--oem 3 --psm 7 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz \'!,♪☆():.-?!" -c user_defined_dpi=300',
            '--oem 3 --psm 8 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz \'!,♪☆():.-?!" -c user_defined_dpi=300',
            '--oem 3 --psm 6 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz \'!,♪☆():.-?!" -c user_defined_dpi=300',
        ]
        for config in configs:
            # Use image_to_data to get confidence scores
            data = pytesseract.image_to_data(img_np, config=config, lang='eng', output_type=pytesseract.Output.DICT)
            
            # Extract text with confidence filtering (>= 90% like event_ocr.py)
            text_parts = []
            for i, word in enumerate(data['text']):
                if word.strip() and data['conf'][i] >= 60:  # Lower threshold to catch more text
                    text_parts.append(word.strip())
            
            text = ' '.join(text_parts).strip()
            
            # Post-processing: Handle common OCR mistakes with special characters
            import re
            # Replace common OCR mistakes for special characters
            text = re.sub(r'\b(Star|star)\b', '☆', text)  # OCR might read ☆ as "Star"
            text = re.sub(r'\b(star)\b', '☆', text)  # Lowercase "star"
            text = re.sub(r'\b(Star)\b', '☆', text)  # Capital "Star"
            
            # Add missing exclamation marks if the event name suggests it
            if 'Escape' in text and not text.endswith('!'):
                text += '!'
            
            # General post-processing: Try to find the best matching event name from database
            text = find_best_event_match(text)
            
            # Post-processing: Remove everything before first uppercase letter
            match = re.search(r'[A-Z]', text)
            if match:
                text = text[match.start():]
            
            # Post-processing: Insert spaces before uppercase letters that follow lowercase letters
            if text:
                text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
            
            if text:
                return text
        return ""
    except Exception as e:
        print(f"[WARNING] Event name OCR extraction failed: {e}")
        return ""

def find_best_event_match(ocr_text):
    """Find the best matching event name from the database using fuzzy matching"""
    try:
        import json
        import os
        from difflib import SequenceMatcher
        
        # Load event databases
        all_event_names = []
        
        # Load support card events
        if os.path.exists("assets/events/support_card.json"):
            with open("assets/events/support_card.json", "r", encoding="utf-8-sig") as f:
                support_events = json.load(f)
                for event in support_events:
                    event_name = event.get("EventName", "")
                    if event_name and event_name not in all_event_names:
                        all_event_names.append(event_name)
        
        # Load uma data events
        if os.path.exists("assets/events/uma_data.json"):
            with open("assets/events/uma_data.json", "r", encoding="utf-8-sig") as f:
                uma_data = json.load(f)
                for character in uma_data:
                    if "UmaEvents" in character:
                        for event in character["UmaEvents"]:
                            event_name = event.get("EventName", "")
                            if event_name and event_name not in all_event_names:
                                all_event_names.append(event_name)
        
        # Find the best match using fuzzy matching
        best_match = ocr_text
        best_ratio = 0.0
        
        # Preprocess OCR text to handle common issues
        clean_ocr_text = ocr_text.strip()
        # Remove trailing quotes and other common OCR artifacts
        clean_ocr_text = clean_ocr_text.rstrip("'\"`").strip()
        
        for db_event_name in all_event_names:
            # Clean the database event name (remove chain symbols)
            clean_db_name = db_event_name.replace("(❯)", "").replace("(❯❯)", "").replace("(❯❯❯)", "").strip()
            
            # Calculate similarity ratio with cleaned OCR text
            ratio = SequenceMatcher(None, clean_ocr_text.lower(), clean_db_name.lower()).ratio()
            
            # Lower threshold to 0.7 for better matching, and also check if OCR text is a prefix
            if (ratio > 0.7 and ratio > best_ratio) or clean_db_name.lower().startswith(clean_ocr_text.lower()):
                best_ratio = ratio
                best_match = db_event_name
        
        # Debug logging
        if best_match != ocr_text:
            debug_print(f"[DEBUG] OCR: '{ocr_text}' -> Matched: '{best_match}' (ratio: {best_ratio:.3f})")
        else:
            debug_print(f"[DEBUG] OCR: '{ocr_text}' -> No match found (best ratio: {best_ratio:.3f})")
        
        return best_match
    except Exception as e:
        print(f"[WARNING] Event name matching failed: {e}")
        return ocr_text

def extract_event_name_text_debug(pil_img: Image.Image, save_prefix: str = "event_debug") -> dict:
    """
    Extract event name text from image using Tesseract OCR with PSM 6, 7, 8.
    Uses the exact same approach as event_ocr.py for consistency.
    """
    import cv2
    import numpy as np
    import pytesseract
    from PIL import ImageDraw

    if isinstance(pil_img, Image.Image):
        img_np = np.array(pil_img)
    else:
        img_np = pil_img
    if img_np.shape[-1] == 4:
        img_np = cv2.cvtColor(img_np, cv2.COLOR_RGBA2RGB)

    # Use the exact same config as event_ocr.py
    config = '-c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz \'!,♪☆():.-?!" -c tessedit_pageseg_mode=7 -c user_defined_dpi=300'
    
    # Use image_to_data to get confidence scores (like event_ocr.py)
    data = pytesseract.image_to_data(img_np, config=config, lang='eng', output_type=pytesseract.Output.DICT)
    
    # Extract text and bounding boxes with confidence filtering (>= 90% like event_ocr.py)
    text_results = []
    full_text = ""
    
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        conf = data['conf'][i]
        
        if text and conf >= 60:  # Lower threshold to catch more text including special characters
            x = data['left'][i]
            y = data['top'][i]
            w = data['width'][i]
            h = data['height'][i]
            
            text_results.append({
                'text': text,
                'confidence': conf,
                'bbox': (x, y, w, h)
            })
            
            full_text += text + " "
    
    full_text = full_text.strip()
    
    # Post-processing: Handle common OCR mistakes with special characters
    import re
    # Replace common OCR mistakes for special characters
    full_text = re.sub(r'\b(Star|star)\b', '☆', full_text)  # OCR might read ☆ as "Star"
    full_text = re.sub(r'\b(star)\b', '☆', full_text)  # Lowercase "star"
    full_text = re.sub(r'\b(Star)\b', '☆', full_text)  # Capital "Star"
    
    # Add missing exclamation marks if the event name suggests it
    if 'Escape' in full_text and not full_text.endswith('!'):
        full_text += '!'
    
    # General post-processing: Try to find the best matching event name from database
    full_text = find_best_event_match(full_text)
    
    # Post-processing: Remove everything before first uppercase letter
    match = re.search(r'[A-Z]', full_text)
    if match:
        full_text = full_text[match.start():]
    
    # Post-processing: Insert spaces before uppercase letters that follow lowercase letters
    if full_text:
        full_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', full_text)
    
    # Calculate average confidence
    if text_results:
        avg_conf = sum(result['confidence'] for result in text_results) / len(text_results) / 100.0
    else:
        avg_conf = 0.0
    
    # Draw bounding boxes
    annotated = pil_img.copy() if isinstance(pil_img, Image.Image) else Image.fromarray(img_np)
    draw = ImageDraw.Draw(annotated)
    for result in text_results:
        x, y, w, h = result['bbox']
        draw.rectangle([x, y, x + w, y + h], outline='red', width=2)
    
    img_path = f"{save_prefix}_result.png"
    annotated.save(img_path)
    
    # Return in the same format as before for compatibility
    results = {
        7: {  # Use PSM 7 as the main result
            'text': full_text,
            'confidence': avg_conf,
            'image_path': img_path,
        }
    }
    
    return results
