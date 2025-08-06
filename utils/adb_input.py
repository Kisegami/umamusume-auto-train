import subprocess
import time
import json

def load_config():
    """Load ADB configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            return config.get('adb_config', {})
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def run_adb_command(command):
    """Run ADB command and return result"""
    try:
        adb_config = load_config()
        adb_path = adb_config.get('adb_path', 'adb')
        device_address = adb_config.get('device_address', '')
        input_delay = adb_config.get('input_delay', 0.5)
        
        # Build the full command
        full_command = [adb_path]
        if device_address:
            full_command.extend(['-s', device_address])
        full_command.extend(command)
        
        # Add delay for input commands
        if 'input' in command:
            time.sleep(input_delay)
        
        # Run the command
        result = subprocess.run(full_command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"ADB command failed: {e}")
        return None
    except Exception as e:
        print(f"Error running ADB command: {e}")
        return None

def tap(x, y):
    """Tap at coordinates (x, y)"""
    return run_adb_command(['shell', 'input', 'tap', str(x), str(y)])

def swipe(start_x, start_y, end_x, end_y, duration_ms=100):
    """Swipe from (start_x, start_y) to (end_x, end_y) with duration in milliseconds"""
    return run_adb_command(['shell', 'input', 'swipe', str(start_x), str(start_y), str(end_x), str(end_y), str(duration_ms)])

def scroll_down():
    """Scroll down on the screen"""
    return swipe(540, 1500, 540, 500, 200)

def scroll_up():
    """Scroll up on the screen"""
    return swipe(540, 500, 540, 1500, 200)

def long_press(x, y, duration_ms=1000):
    """Long press at coordinates (x, y) for duration_ms milliseconds"""
    return swipe(x, y, x, y, duration_ms)

def mouse_down(x, y):
    """Simulate mouse down at coordinates (x, y)"""
    return run_adb_command(['shell', 'input', 'touchscreen', 'swipe', str(x), str(y), str(x), str(y), '100'])

def mouse_up(x, y):
    """Simulate mouse up at coordinates (x, y)"""
    return run_adb_command(['shell', 'input', 'touchscreen', 'swipe', str(x), str(y), str(x), str(y), '100'])

def triple_click(x, y, interval=0.1):
    """Perform triple click at coordinates (x, y)"""
    for i in range(3):
        tap(x, y)
        if i < 2:  # Don't wait after the last click
            time.sleep(interval)

def click_at_coordinates(x, y):
    """Click at specific coordinates (alias for tap)"""
    return tap(x, y)

def move_to_and_click(x, y):
    """Move to coordinates and click (alias for tap)"""
    return tap(x, y) 