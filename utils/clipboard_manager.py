# utils/clipboard_manager.py
import threading
import tkinter as tk
import time

class ClipboardManager:
    def __init__(self):
        self.lock = threading.RLock()
        self._clipboard_data = {}
    
    def get_clipboard(self, device_id):
        """Get clipboard content for specific device with retry mechanism."""
        with self.lock:
            retry_attempts = 5
            for attempt in range(retry_attempts):
                try:
                    root = tk.Tk()
                    root.withdraw()
                    data = root.clipboard_get()
                    root.destroy()
                    
                    # Store this data for this device
                    self._clipboard_data[device_id] = data
                    return data
                except tk.TclError:
                    print(f"Device {device_id}: Can't access clipboard. Retrying...")
                    time.sleep(0.5)
            
            # Return last known value for this device or default
            return self._clipboard_data.get(device_id, "Unknown")