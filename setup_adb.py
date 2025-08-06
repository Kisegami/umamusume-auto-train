#!/usr/bin/env python3
"""
ADB Setup Helper Script
This script helps you configure ADB connection settings
"""

import subprocess
import json
import os
import sys

def load_config():
    """Load current configuration"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("config.json not found! Please make sure you're in the project directory.")
        return {}
    except json.JSONDecodeError:
        print("Error reading config.json! Please check the file format.")
        return {}

def save_config(config):
    """Save configuration to file"""
    try:
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        print("✓ Configuration saved successfully!")
        return True
    except Exception as e:
        print("✗ Error saving configuration: " + str(e))
        return False

def check_adb_installation():
    """Check if ADB is installed"""
    try:
        result = subprocess.run(['adb', 'version'], capture_output=True, text=True, check=True)
        print("✓ ADB found: " + result.stdout.split('\n')[0])
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ ADB not found!")
        print("Please install Android SDK and add ADB to your PATH")
        print("Download from: https://developer.android.com/studio/releases/platform-tools")
        return False

def list_available_devices():
    """List all available ADB devices"""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        devices = []
        
        for line in lines:
            if line.strip() and '\tdevice' in line:
                device_id = line.split('\t')[0]
                devices.append(device_id)
        
        return devices
    except Exception as e:
        print("Error listing devices: " + str(e))
        return []

def get_device_info(device_id):
    """Get information about a specific device"""
    try:
        # Get device model
        model_result = subprocess.run(['adb', '-s', device_id, 'shell', 'getprop', 'ro.product.model'], 
                                    capture_output=True, text=True, check=True)
        model = model_result.stdout.strip()
        
        # Get Android version
        version_result = subprocess.run(['adb', '-s', device_id, 'shell', 'getprop', 'ro.build.version.release'], 
                                      capture_output=True, text=True, check=True)
        version = version_result.stdout.strip()
        
        # Get screen size
        size_result = subprocess.run(['adb', '-s', device_id, 'shell', 'wm', 'size'], 
                                   capture_output=True, text=True, check=True)
        size_str = size_result.stdout.strip().split(': ')[1]
        
        return {
            'model': model,
            'version': version,
            'screen_size': size_str
        }
    except Exception as e:
        print("Error getting device info: " + str(e))
        return {}

def setup_adb_config():
    """Interactive ADB configuration setup"""
    print("ADB Configuration Setup")
    print("=" * 40)
    
    # Check ADB installation
    if not check_adb_installation():
        return False
    
    # Load current config
    config = load_config()
    if not config:
        return False
    
    # Initialize adb_config if not present
    if 'adb_config' not in config:
        config['adb_config'] = {}
    
    adb_config = config['adb_config']
    
    print("\nCurrent ADB Configuration:")
    print("  Device Address: " + adb_config.get('device_address', 'Not set'))
    print("  ADB Path: " + adb_config.get('adb_path', 'adb'))
    print("  Input Delay: " + str(adb_config.get('input_delay', 0.5)) + "s")
    print("  Screenshot Timeout: " + str(adb_config.get('screenshot_timeout', 5)) + "s")
    
    # List available devices
    print("\nAvailable ADB Devices:")
    devices = list_available_devices()
    
    if not devices:
        print("  No devices found!")
        print("\nTo connect a device:")
        print("1. Enable USB debugging on your Android device")
        print("2. Connect via USB or start an emulator")
        print("3. Run 'adb devices' to verify connection")
        print("4. Run this script again")
        return False
    
    for i, device in enumerate(devices, 1):
        print(f"  {i}. {device}")
        device_info = get_device_info(device)
        if device_info:
            print(f"     Model: {device_info.get('model', 'Unknown')}")
            print(f"     Android: {device_info.get('version', 'Unknown')}")
            print(f"     Screen: {device_info.get('screen_size', 'Unknown')}")
    
    # Device selection
    print("\nDevice Selection:")
    print("1. Use first available device")
    print("2. Specify device address manually")
    print("3. Skip device configuration")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == '1':
        if devices:
            adb_config['device_address'] = devices[0]
            print("✓ Using device: " + devices[0])
        else:
            print("✗ No devices available")
            return False
    elif choice == '2':
        device_address = input("Enter device address (e.g., 127.0.0.1:5555): ").strip()
        if device_address:
            adb_config['device_address'] = device_address
            print("✓ Device address set to: " + device_address)
        else:
            print("✗ Invalid device address")
            return False
    elif choice == '3':
        print("Skipping device configuration")
    else:
        print("✗ Invalid choice")
        return False
    
    # ADB path configuration
    print("\nADB Path Configuration:")
    print("Current ADB path: " + adb_config.get('adb_path', 'adb'))
    
    custom_path = input("Enter custom ADB path (or press Enter to use default): ").strip()
    if custom_path:
        adb_config['adb_path'] = custom_path
        print("✓ ADB path set to: " + custom_path)
    
    # Timing configuration
    print("\nTiming Configuration:")
    
    try:
        input_delay = float(input(f"Input delay in seconds (current: {adb_config.get('input_delay', 0.5)}): ") or adb_config.get('input_delay', 0.5))
        adb_config['input_delay'] = input_delay
        print("✓ Input delay set to: " + str(input_delay) + "s")
    except ValueError:
        print("✗ Invalid input delay value")
        return False
    
    try:
        screenshot_timeout = int(input(f"Screenshot timeout in seconds (current: {adb_config.get('screenshot_timeout', 5)}): ") or adb_config.get('screenshot_timeout', 5))
        adb_config['screenshot_timeout'] = screenshot_timeout
        print("✓ Screenshot timeout set to: " + str(screenshot_timeout) + "s")
    except ValueError:
        print("✗ Invalid screenshot timeout value")
        return False
    
    # Save configuration
    print("\nSaving configuration...")
    if save_config(config):
        print("\n✓ ADB configuration completed successfully!")
        print("\nNext steps:")
        print("1. Run: python test_adb_setup.py")
        print("2. Adjust regions in utils/constants_phone.py")
        print("3. Run: python main_adb.py")
        return True
    else:
        return False

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("ADB Setup Helper Script")
        print("\nUsage:")
        print("  python setup_adb.py          # Interactive setup")
        print("  python setup_adb.py --help   # Show this help")
        print("\nThis script helps you configure ADB connection settings")
        print("for the Uma Auto Train project.")
        return
    
    try:
        success = setup_adb_config()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print("Setup error: " + str(e))
        sys.exit(1)

if __name__ == "__main__":
    main() 