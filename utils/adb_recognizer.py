import cv2
import numpy as np
from PIL import Image
import os
from utils.adb_screenshot import take_screenshot

def match_template(screenshot, template_path, confidence=0.8, region=None):
    """
    Match template image on screenshot using OpenCV
    
    Args:
        screenshot: PIL Image of the screen
        template_path: Path to template image
        confidence: Minimum confidence threshold
        region: Region to search in (x, y, width, height)
    
    Returns:
        List of (x, y, width, height) matches or None if not found
    """
    try:
        # Load template
        if not os.path.exists(template_path):
            print(f"Template not found: {template_path}")
            return None
        
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            print(f"Failed to load template: {template_path}")
            return None
        
        # Convert screenshot to OpenCV format
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # Crop to region if specified
        if region:
            x, y, w, h = region
            screenshot_cv = screenshot_cv[y:y+h, x:x+w]
        
        # Get template dimensions
        h, w = template.shape[:2]
        
        # Perform template matching
        result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
        
        # Find locations where the matching exceeds the threshold
        locations = np.where(result >= confidence)
        matches = []
        
        for pt in zip(*locations[::-1]):  # Switch columns and rows
            if region:
                # Adjust coordinates back to full screen
                pt = (pt[0] + region[0], pt[1] + region[1])
            
            matches.append((pt[0], pt[1], w, h))
        
        return matches if matches else None
        
    except Exception as e:
        print(f"Error in template matching: {e}")
        return None

def locate_on_screen(template_path, confidence=0.8, region=None):
    """
    Locate template on screen and return center coordinates
    
    Args:
        template_path: Path to template image
        confidence: Minimum confidence threshold
        region: Region to search in (x, y, width, height)
    
    Returns:
        (x, y) center coordinates or None if not found
    """
    screenshot = take_screenshot()
    matches = match_template(screenshot, template_path, confidence, region)
    
    if matches:
        # Return center of first match
        x, y, w, h = matches[0]
        return (x + w//2, y + h//2)
    
    return None

def locate_all_on_screen(template_path, confidence=0.8, region=None):
    """
    Locate all instances of template on screen
    
    Args:
        template_path: Path to template image
        confidence: Minimum confidence threshold
        region: Region to search in (x, y, width, height)
    
    Returns:
        List of (x, y, width, height) matches or empty list if not found
    """
    screenshot = take_screenshot()
    matches = match_template(screenshot, template_path, confidence, region)
    
    return matches if matches else []

def locate_center_on_screen(template_path, confidence=0.8, region=None):
    """
    Locate template on screen and return center coordinates (alias for locate_on_screen)
    """
    return locate_on_screen(template_path, confidence, region)

def is_image_on_screen(template_path, confidence=0.8, region=None):
    """
    Check if template image is present on screen
    
    Args:
        template_path: Path to template image
        confidence: Minimum confidence threshold
        region: Region to search in (x, y, width, height)
    
    Returns:
        True if found, False otherwise
    """
    return locate_on_screen(template_path, confidence, region) is not None

def wait_for_image(template_path, timeout=10, confidence=0.8, region=None):
    """
    Wait for image to appear on screen
    
    Args:
        template_path: Path to template image
        timeout: Maximum time to wait in seconds
        confidence: Minimum confidence threshold
        region: Region to search in (x, y, width, height)
    
    Returns:
        (x, y) center coordinates or None if timeout
    """
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        result = locate_on_screen(template_path, confidence, region)
        if result:
            return result
        time.sleep(0.1)
    
    return None 