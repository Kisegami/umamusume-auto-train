import time
import subprocess
import json
from utils.adb_screenshot import run_adb_command, get_screen_size, load_config
from core.execute_adb import career_lobby

def check_adb_connection():
    """Check if ADB is connected to a device"""
    config = load_config()
    adb_path = config.get('adb_path', 'adb')
    
    try:
        result = subprocess.run([adb_path, 'devices'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')[1:]  # Skip header line
        connected_devices = [line for line in lines if line.strip() and '\tdevice' in line]
        
        if not connected_devices:
            print("No ADB devices connected!")
            print("Please connect your Android device or emulator and enable USB debugging.")
            return False
        
        print("Connected devices: " + str(len(connected_devices)))
        for device in connected_devices:
            print("  " + device.split('\t')[0])
        return True
        
    except subprocess.CalledProcessError:
        print("ADB not found! Please install Android SDK and add ADB to your PATH.")
        return False
    except FileNotFoundError:
        print("ADB not found! Please install Android SDK and add ADB to your PATH.")
        return False

def get_device_info():
    """Get device information"""
    try:
        # Get screen size
        width, height = get_screen_size()
        print("Device screen size: " + str(width) + "x" + str(height))
        
        # Get device model
        model = run_adb_command(['shell', 'getprop', 'ro.product.model'])
        if model:
            print("Device model: " + model)
        
        # Get Android version
        version = run_adb_command(['shell', 'getprop', 'ro.build.version.release'])
        if version:
            print("Android version: " + version)
            
        return True
        
    except Exception as e:
        print("Error getting device info: " + str(e))
        return False

def main():
    print("Uma Auto - ADB Version!")
    print("=" * 40)
    
    # Check ADB connection
    if not check_adb_connection():
        return
    
    # Get device information
    if not get_device_info():
        return
    
    print("\nStarting automation...")
    print("Make sure Umamusume is running on your device!")
    print("Press Ctrl+C to stop the automation.")
    print("=" * 40)
    
    try:
        career_lobby()
    except KeyboardInterrupt:
        print("\nAutomation stopped by user.")
    except Exception as e:
        print("\nAutomation error: " + str(e))

if __name__ == "__main__":
    main() 