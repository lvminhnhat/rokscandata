# main.py
import os
import sys
import argparse
from utils.config_manager import load_config
from ui.main_window import MainWindow
from scanner.scan_manager import ScanManager

def main():
    parser = argparse.ArgumentParser(description='RokTracker Multi-Device')
    parser.add_argument('--config', type=str, help='Path to config file')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Create required directories
    os.makedirs(config.data_dir, exist_ok=True)
    os.makedirs(config.logs_dir, exist_ok=True)
    os.makedirs(config.screenshots_dir, exist_ok=True)
    
    # Create scan manager
    scan_manager = ScanManager(config)
    
    # Start GUI if not in command line mode
    if not config.cli_mode:
        app = MainWindow(config)
        app.mainloop()
    else:
        # Run in CLI mode
        pass

if __name__ == "__main__":
    main()