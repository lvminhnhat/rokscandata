# ui/main_window.py
import tkinter as tk
from tkinter import ttk
from ui.device_manager import DeviceManagerFrame
from ui.scan_panel import ScanPanel
import os
import queue
import threading

class MainWindow(tk.Tk):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.title("RokTracker Multi-Device")
        self.geometry("800x600")
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)
        
        # Khởi tạo ScanManager 
        from scanner.scan_manager import ScanManager
        self.scan_manager = ScanManager(config)
        self.scan_manager.window = self
        
        # Device manager tab - khởi tạo trước để scan_panel có thể sử dụng
        self.device_manager = DeviceManagerFrame(self.notebook, config)
        self.notebook.add(self.device_manager, text="Device Manager")
        
        # Scan tab - truyền tham chiếu của main_window trực tiếp
        self.scan_panel = ScanPanel(self.notebook, config)
        self.scan_panel.main_window = self  # Đảm bảo scan_panel có tham chiếu đến main_window
        self.notebook.add(self.scan_panel, text="Scan")
        
        # Settings tab
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Settings")
        
        # Status bar
        self.status_bar = ttk.Frame(self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        # Credits
        credits_label = ttk.Label(self.status_bar, text="RokTracker Multi-Device")
        credits_label.pack(side=tk.RIGHT)
        
        # Thiết lập liên kết giữa các thành phần
        self.scan_manager.device_manager = self.device_manager

    def get_device_manager(self):
        """Trả về thể hiện của device manager"""
        return self.device_manager

    def get_scan_manager(self):
        """Trả về thể hiện của scan manager"""
        return self.scan_manager