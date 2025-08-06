import subprocess
import tempfile
import os
import json
from PIL import Image, ImageEnhance
import numpy as np

def load_config():
    """Load ADB configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            return config.get('adb_config', {})
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def run_adb_command(command, binary=False):
    """Run ADB command and return result"""
    try:
        adb_config = load_config()
        adb_path = adb_config.get('adb_path', 'adb')
        device_address = adb_config.get('device_address', '')
        
        # Build the full command
        full_command = [adb_path]
        if device_address:
            full_command.extend(['-s', device_address])
        full_command.extend(command)
        
        # Run the command
        if binary:
            result = subprocess.run(full_command, capture_output=True, check=True)
            return result.stdout
        else:
            result = subprocess.run(full_command, capture_output=True, text=True, check=True)
            return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"ADB command failed: {e}")
        return None
    except Exception as e:
        print(f"Error running ADB command: {e}")
        return None

def take_screenshot():
    """Take a screenshot using ADB and return PIL Image"""
    try:
        result = run_adb_command(['shell', 'screencap'], binary=True)
        if result is None:
            raise Exception("Failed to take screenshot")
        
        cleaned_result = result.replace(b'\r\n', b'\n') # Remove carriage returns
        
        # Parse the header: width (4 bytes), height (4 bytes), format (4 bytes), unknown (4 bytes)
        width = int.from_bytes(cleaned_result[0:4], byteorder='little')
        height = int.from_bytes(cleaned_result[4:8], byteorder='little')
        # format_info = int.from_bytes(cleaned_result[8:12], byteorder='little') # Not used directly
        
        pixel_data = cleaned_result[16:] # Skip the header (16 bytes)
        
        img = Image.frombytes('RGBA', (width, height), pixel_data) # Create image from raw pixel data
        return img
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        raise

def enhanced_screenshot(region):
    """Take a screenshot of a specific region with enhancement (same as PC version)"""
    try:
        screenshot = take_screenshot()
        cropped = screenshot.crop(region)
        
        # Resize for better OCR (same as PC version)
        cropped = cropped.resize((cropped.width * 2, cropped.height * 2), Image.BICUBIC)
        
        # Convert to grayscale (same as PC version)
        cropped = cropped.convert("L")
        
        # Enhance contrast (same as PC version)
        enhancer = ImageEnhance.Contrast(cropped)
        enhanced = enhancer.enhance(1.5)
        
        return enhanced
    except Exception as e:
        print(f"Error taking enhanced screenshot: {e}")
        raise

def enhanced_screenshot_for_failure(region):
    """Enhanced screenshot specifically optimized for white and yellow text on orange background"""
    try:
        screenshot = take_screenshot()
        cropped = screenshot.crop(region)
        
        # Resize for better OCR
        cropped = cropped.resize((cropped.width * 2, cropped.height * 2), Image.BICUBIC)
        
        # Convert to RGB to work with color channels
        cropped = cropped.convert("RGB")
        
        # Convert to numpy for color processing
        img_np = np.array(cropped)
        
        # Define orange color range (RGB) - for background
        # Orange background typically has high red, medium green, low blue
        orange_mask = (
            (img_np[:, :, 0] > 150) &  # High red
            (img_np[:, :, 1] > 80) &   # Medium green  
            (img_np[:, :, 2] < 100)    # Low blue
        )
        
        # Define white text range (RGB) - for "Failure" text
        white_mask = (
            (img_np[:, :, 0] > 200) &  # High red
            (img_np[:, :, 1] > 200) &  # High green
            (img_np[:, :, 2] > 200)    # High blue
        )
        
        # Define yellow text range (RGB) - for failure rate percentages
        # Yellow: (255, 210, 17) - high red, high green, low blue
        # Using more permissive thresholds to catch yellow text
        yellow_mask = (
            (img_np[:, :, 0] > 190) &  # High red
            (img_np[:, :, 1] > 140) &  # High green
            (img_np[:, :, 2] < 90)     # Low blue
        )
        
        # Create a new image: black background, white and yellow text
        result = np.zeros_like(img_np)
        
        # Set white text (for "Failure")
        result[white_mask] = [255, 255, 255]
        
        # Set yellow text (for percentages) - convert to white for OCR
        result[yellow_mask] = [255, 255, 255]
        
        # Set orange background to black
        result[orange_mask] = [0, 0, 0]
        
        # Convert back to PIL
        pil_img = Image.fromarray(result)
        
        # Convert to grayscale for OCR
        pil_img = pil_img.convert("L")
        
        # Enhance contrast for better OCR
        pil_img = ImageEnhance.Contrast(pil_img).enhance(1.5)
        
        return pil_img
    except Exception as e:
        print(f"Error taking failure screenshot: {e}")
        raise

def enhanced_screenshot_for_year(region):
    """Take a screenshot optimized for year detection"""
    try:
        screenshot = take_screenshot()
        cropped = screenshot.crop(region)
        
        # Enhance for year text detection
        enhancer = ImageEnhance.Contrast(cropped)
        enhanced = enhancer.enhance(2.5)
        
        enhancer = ImageEnhance.Sharpness(enhanced)
        enhanced = enhancer.enhance(2.0)
        
        return enhanced
    except Exception as e:
        print(f"Error taking year screenshot: {e}")
        raise

def capture_region(region):
    """Capture a specific region of the screen"""
    try:
        screenshot = take_screenshot()
        return screenshot.crop(region)
    except Exception as e:
        print(f"Error capturing region: {e}")
        raise

def get_screen_size():
    """Get the screen size of the connected device"""
    try:
        # Get screen size using wm size command
        result = run_adb_command(['shell', 'wm', 'size'])
        if result:
            # Parse output like "Physical size: 1080x1920"
            if 'Physical size:' in result:
                size_part = result.split('Physical size:')[1].strip()
                width, height = map(int, size_part.split('x'))
                return width, height
            else:
                # Fallback: parse direct size output
                width, height = map(int, result.split('x'))
                return width, height
        else:
            # Fallback: take a screenshot and get its size
            screenshot = take_screenshot()
            return screenshot.size
    except Exception as e:
        print(f"Error getting screen size: {e}")
        # Default fallback size
        return 1080, 1920 