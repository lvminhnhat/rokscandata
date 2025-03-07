# utils/config_manager.py
import json
import os
from dataclasses import dataclass
from typing import List, Dict, Any
from types import SimpleNamespace

@dataclass
class Config:
    tesseract_path: str
    ldplayer_path: str
    data_dir: str
    logs_dir: str
    screenshots_dir: str
    devices_file: str
    cli_mode: bool = False
    scan_option: int = 1  # Added scan_option with default value of 1 (full scan)
    
    @classmethod
    def from_dict(cls, config_dict):
        return cls(
            tesseract_path=config_dict.get('tesseract_path', ''),
            ldplayer_path=config_dict.get('ldplayer_path', ''),
            data_dir=config_dict.get('data_dir', 'data'),
            logs_dir=config_dict.get('logs_dir', 'logs'),
            screenshots_dir=config_dict.get('screenshots_dir', 'screenshots'),
            devices_file=config_dict.get('devices_file', 'config/devices.json'),
            cli_mode=config_dict.get('cli_mode', False),
            scan_option=config_dict.get('scan_option', 1)  # Add scan_option to the constructor
        )

# Default configuration
DEFAULT_CONFIG = {
    "tesseract_path": r"D:\Code\rok\scanData\roktrackerRemake\roktrackerRemake\Tesseract-OCR\tesseract.exe",
    "ldplayer_path": r"C:\LDPlayer\LDPlayer4.0",
    "data_dir": "data",
    "screenshots_dir": "screenshots",
    "logs_dir": "logs",
    "devices_file": "devices.json",
    "cli_mode": False,
    "scan_option": 1,  # Added scan_option to default config
    "version": "10.1",
    "debug": True
}

def load_config(config_path=None):
    """
    Load configuration from file or use default if file doesn't exist
    
    Args:
        config_path (str, optional): Path to config file. Defaults to None.
        
    Returns:
        SimpleNamespace: Configuration as object with attribute access
    """
    config_data = DEFAULT_CONFIG.copy()
    
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                config_data.update(file_config)
        except Exception as e:
            print(f"Error loading config file: {e}")
    
    # Convert data dict directories to absolute paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for key in ["data_dir", "screenshots_dir", "logs_dir"]:
        if not os.path.isabs(config_data[key]):
            config_data[key] = os.path.join(base_dir, config_data[key])
    
    # Make devices file path absolute if it's not already
    if not os.path.isabs(config_data["devices_file"]):
        config_data["devices_file"] = os.path.join(
            config_data["data_dir"], config_data["devices_file"]
        )
    
    return SimpleNamespace(**config_data)

def save_config(config, config_path):
    """
    Save configuration to file
    
    Args:
        config (SimpleNamespace): Configuration object
        config_path (str): Path to save config file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(config_path, 'w') as f:
            json.dump(vars(config), f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config file: {e}")
        return False