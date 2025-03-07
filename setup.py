import os
import subprocess
import sys
import platform

def main():
    """Setup the environment for RokTracker"""
    print("Setting up RokTracker environment...")
    
    # Cài đặt các package cần thiết
    packages = [
        "numpy==1.23.5",
        "opencv-python==4.5.5.64",
        "pytesseract==0.3.9",
        "pillow==9.3.0",
        "xlwt==1.3.0"
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError as e:
            print(f"Error installing {package}: {e}")
            return
    
    # Tạo các thư mục cần thiết
    dirs = ["data", "data/scan_results", "screenshots", "logs", "config"]
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
    
    # Tạo file config.json nếu chưa tồn tại
    config_path = "config/config.json"
    if not os.path.exists(config_path):
        import json
        config = {
            "tesseract_path": os.path.join(os.getcwd(), "Tesseract-OCR", "tesseract.exe"),
            "ldplayer_path": "C:\\LDPlayer\\LDPlayer4.0",
            "data_dir": "data",
            "logs_dir": "logs",
            "screenshots_dir": "screenshots",
            "devices_file": "data/devices.json",
            "cli_mode": False,
            "scan_option": 1
        }
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
    
    print("Setup complete!")
    print("\nYou can now run the application with:")
    print("python roktrackerRemake/main.py")
    
if __name__ == "__main__":
    main()