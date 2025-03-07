import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

class ScanPanel(ttk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.parent = parent
        self.main_window = self._get_main_window()
        
        # Dictionary để theo dõi các mục trong scan_tree
        self.scan_items = {}
        
        # Khởi tạo device_ids và UI
        self.device_ids = {}
        self.setup_ui()
        
        # Bắt đầu timer cập nhật
        self._start_update_timer()
    
    def _get_main_window(self):
        """Tìm đối tượng MainWindow trong cây phân cấp"""
        parent = self.master
        # Đi ngược lên cho đến khi tìm thấy MainWindow
        while parent and not hasattr(parent, 'get_device_manager'):
            parent = parent.master
        return parent
        
    def setup_ui(self):
        # Configure grid weights for proper stretching
        self.columnconfigure(0, weight=1)
        for i in range(5):  # Adjust rows to properly space elements
            self.rowconfigure(i, weight=1 if i == 3 else 0)
        
        # Header frame - Top row
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Kingdom Name and Search Amount inputs
        ttk.Label(header_frame, text="Kingdom Name:").pack(side=tk.LEFT, padx=5)
        self.kingdom_var = tk.StringVar()
        ttk.Entry(header_frame, textvariable=self.kingdom_var, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(header_frame, text="Search Amount:").pack(side=tk.LEFT, padx=5)
        self.search_range_var = tk.IntVar(value=50)
        options = [50 + i * 25 for i in range(38)]
        ttk.Combobox(header_frame, textvariable=self.search_range_var, values=options, width=5).pack(side=tk.LEFT, padx=5)
        
        self.resume_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(header_frame, text="Resume Scan", variable=self.resume_var).pack(side=tk.LEFT, padx=5)
        
        # Scan options frame - Clear and separate section
        options_frame = ttk.LabelFrame(self, text="Scan Options")
        options_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # Set scan option from config and ensure buttons are clearly visible
        self.scan_option_var = tk.IntVar(value=getattr(self.config, 'scan_option', 1))
        
        # Use pack instead of grid for more predictable layout
        ttk.Radiobutton(options_frame, text="Full Scan", variable=self.scan_option_var, value=1).pack(anchor=tk.W, padx=20, pady=5)
        ttk.Radiobutton(options_frame, text="Power + Kill Points Only", variable=self.scan_option_var, value=2).pack(anchor=tk.W, padx=20, pady=5)
        ttk.Radiobutton(options_frame, text="Power + Kill Points + Dead Points", variable=self.scan_option_var, value=3).pack(anchor=tk.W, padx=20, pady=5)
        
        # Device selection with more space
        devices_frame = ttk.LabelFrame(self, text="Available Devices")
        devices_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        # Use pack with expand/fill for better sizing
        device_frame_inner = ttk.Frame(devices_frame)
        device_frame_inner.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbars to the listbox
        scrollbar = ttk.Scrollbar(device_frame_inner)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.device_listbox = tk.Listbox(device_frame_inner, selectmode=tk.MULTIPLE, height=4)
        self.device_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.device_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.device_listbox.yview)
        
        # Refresh devices button
        ttk.Button(devices_frame, text="Refresh Devices", command=self.refresh_devices).pack(pady=5)
        
        # Currently active scans (makes this bigger as it needs more space)
        active_scans_frame = ttk.LabelFrame(self, text="Active Scans")
        active_scans_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        
        # Add a proper scrollbar to the treeview
        tree_frame = ttk.Frame(active_scans_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ('device', 'kingdom', 'progress', 'eta')
        self.scan_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=6)
        
        # Configure column widths
        self.scan_tree.column('device', width=80)
        self.scan_tree.column('kingdom', width=120)
        self.scan_tree.column('progress', width=80)
        self.scan_tree.column('eta', width=80)
        
        self.scan_tree.heading('device', text='Device')
        self.scan_tree.heading('kingdom', text='Kingdom')
        self.scan_tree.heading('progress', text='Progress')
        self.scan_tree.heading('eta', text='ETA')
        
        # Add scrollbar to treeview
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.scan_tree.yview)
        self.scan_tree.configure(yscrollcommand=tree_scroll.set)
        
        # Pack treeview and scrollbar
        self.scan_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Control buttons frame (bottom row)
        control_frame = ttk.Frame(self)
        control_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=10)
        
        # Give more room to buttons
        ttk.Button(control_frame, text="Start Scan", command=self.start_scan).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="Stop Selected", command=self.stop_selected).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="Stop All", command=self.stop_all).pack(side=tk.LEFT, padx=10)
    
    def refresh_devices(self):
        """Update the device list with currently available devices"""
        self.device_listbox.delete(0, tk.END)
        
        # Store device IDs in a separate dictionary
        self.device_ids = {}  # Add this as an instance variable
        
        # Lấy tham chiếu đến device manager từ MainWindow
        if self.main_window:
            device_manager = self.main_window.get_device_manager()
            
            if device_manager and hasattr(device_manager, 'get_available_devices'):
                try:
                    # Chỉ lấy các thiết bị khả dụng
                    available_devices = device_manager.get_available_devices()
                    
                    for i, device in enumerate(available_devices):
                        display_text = f"{device['name']} (ID: {device['id']})"
                        self.device_listbox.insert(tk.END, display_text)
                        # Store device ID in our dictionary with the index as the key
                        self.device_ids[i] = device['id']
                except Exception as e:
                    print(f"Error refreshing devices: {e}")
                    messagebox.showerror("Error", f"Failed to refresh devices: {str(e)}")
            else:
                print("Device manager not available or missing get_available_devices method")
                self._add_mock_devices()
        else:
            print("Main window not found")
            self._add_mock_devices()
    
    def _add_mock_devices(self):
        """Add mock devices for testing when real devices can't be loaded"""
        # Initialize device_ids dictionary if it doesn't exist
        if not hasattr(self, 'device_ids'):
            self.device_ids = {}
            
        for i in range(3):
            self.device_listbox.insert(tk.END, f"Mock Device {i} (ID: {i})")
            self.device_ids[i] = str(i)
        messagebox.showinfo("Mock Devices", "Using mock devices for testing.")
    
    def _start_update_timer(self):
        """Bắt đầu timer cập nhật trạng thái quét định kỳ"""
        def update_scan_status():
            self.update_scan_progress()
            # Chạy lại sau 1 giây
            self.after(1000, update_scan_status)
        
        # Bắt đầu timer
        self.after(1000, update_scan_status)
    
    def update_scan_progress(self):
        """Cập nhật trạng thái tiến trình quét trong UI"""
        if self.main_window and hasattr(self.main_window, 'get_scan_manager'):
            scan_manager = self.main_window.get_scan_manager()
            if scan_manager:
                active_scans = scan_manager.get_active_scans()
                
                # Cập nhật từng quét đang chạy
                for device_id, scan_info in active_scans.items():
                    progress = scan_info.get("progress", 0)
                    
                    # Tính ETA
                    start_time = scan_info.get("start_time", time.time())
                    elapsed = time.time() - start_time
                    
                    if progress > 0:
                        total_time = elapsed * 100 / progress
                        remaining = total_time - elapsed
                        eta = self._format_time(remaining)
                    else:
                        eta = "Calculating..."
                    
                    # Tìm item trong tree để cập nhật
                    if device_id in self.scan_items:
                        item_id = self.scan_items[device_id]
                        item_values = self.scan_tree.item(item_id, 'values')
                        
                        if item_values:
                            # Cập nhật chỉ tiến trình và ETA
                            self.scan_tree.item(item_id, values=(
                                item_values[0],
                                item_values[1],
                                f"{progress}%",
                                eta
                            ))
    
    def _format_time(self, seconds):
        """Format số giây thành MM:SS"""
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def start_scan(self):
        """Start scanning on selected devices"""
        selected_indices = self.device_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Device Selected", "Please select at least one device to start scanning.")
            return
            
        kingdom = self.kingdom_var.get()
        if not kingdom:
            messagebox.showwarning("Missing Information", "Please enter a kingdom name.")
            return
            
        # Get scan parameters
        scan_params = {
            'kingdom': kingdom,
            'search_range': self.search_range_var.get(),
            'resume_scanning': self.resume_var.get(),
            'scan_option': self.scan_option_var.get()
        }
        
        # Get scan manager from main window
        scan_manager = None
        if self.main_window and hasattr(self.main_window, 'get_scan_manager'):
            scan_manager = self.main_window.get_scan_manager()
            
            # Đặt callback cho scan_manager
            if scan_manager:
                scan_manager.ui_callback = self.handle_scan_event
        
        success_count = 0
        for idx in selected_indices:
            # Get device ID from our dictionary using the selected index
            device_id = self.device_ids.get(idx)
            display_name = self.device_listbox.get(idx)
            
            if not device_id:
                print(f"Could not find device ID for index {idx}")
                continue
                
            print(f"Starting scan on device {device_id} ({display_name})")
            
            # If we have a scan manager, use it to start the scan
            if scan_manager:
                try:
                    if scan_manager.start_scan(device_id, scan_params):
                        success_count += 1
                        item_id = self.scan_tree.insert('', 'end', 
                                              values=(display_name, kingdom, "0%", "Calculating..."))
                        # Lưu item_id để có thể cập nhật sau này
                        self.scan_items[str(device_id)] = item_id
                    else:
                        print(f"Failed to start scan on device {device_id}")
                except Exception as e:
                    print(f"Error starting scan: {e}")
            else:
                # Mock adding to the scan tree for testing UI
                item_id = self.scan_tree.insert('', 'end', 
                                      values=(display_name, kingdom, "0%", "Calculating..."))
                self.scan_items[str(device_id)] = item_id
                success_count += 1
        
        if success_count > 0:
            messagebox.showinfo("Scan Started", f"Started scanning on {success_count} device(s).")
        else:
            messagebox.showerror("Error", "Failed to start scanning on any device.")
    
    def handle_scan_event(self, event_type, data):
        """
        Xử lý các sự kiện từ ScanManager
        
        Args:
            event_type (str): Loại sự kiện (progress_update, scan_completed, scan_error)
            data (dict): Dữ liệu sự kiện
        """
        if event_type == "progress_update":
            device_id = data.get("device_id")
            progress = data.get("progress", 0)
            message = data.get("message", "")
            
            # Cập nhật UI có thể thêm ở đây nếu cần
            # Nhưng đã có phương thức update_scan_progress chạy định kỳ
            
        elif event_type == "scan_completed":
            device_id = data.get("device_id")
            output_file = data.get("output_file", "")
            message = data.get("message", "")
            
            # Thông báo hoàn thành
            self.after(0, lambda: messagebox.showinfo("Scan Completed", 
                                  f"Scan completed for device {device_id}.\nResults saved to {output_file}"))
            
            # Xóa khỏi active scans trong UI
            if device_id in self.scan_items:
                item_id = self.scan_items[device_id]
                self.after(0, lambda: self.scan_tree.delete(item_id))
                del self.scan_items[device_id]
            
        elif event_type == "scan_error":
            device_id = data.get("device_id")
            error = data.get("error", "Unknown error")
            
            # Thông báo lỗi
            self.after(0, lambda: messagebox.showerror("Scan Error", 
                                  f"Error during scan on device {device_id}: {error}"))
            
            # Xóa khỏi active scans trong UI
            if device_id in self.scan_items:
                item_id = self.scan_items[device_id]
                self.after(0, lambda: self.scan_tree.delete(item_id))
                del self.scan_items[device_id]
    
    def stop_selected(self):
        """Stop scanning on selected devices"""
        selected_items = self.scan_tree.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select a scan to stop.")
            return
            
        # Get scan manager
        scan_manager = None
        if self.main_window and hasattr(self.main_window, 'get_scan_manager'):
            scan_manager = self.main_window.get_scan_manager()
        
        # Stop each selected scan
        for item in selected_items:
            device_info = self.scan_tree.item(item, 'values')[0]
            print(f"Stopping scan on device: {device_info}")
            
            # Try to extract device ID
            import re
            match = re.search(r'ID: (\d+)', device_info)
            if match and scan_manager:
                device_id = match.group(1)
                scan_manager.stop_scan(device_id)
            else:
                # Fallback if can't extract ID or no scan_manager
                self.scan_tree.delete(item)
                # Remove from scan_items if it exists
                for device_id, item_id in list(self.scan_items.items()):
                    if item_id == item:
                        del self.scan_items[device_id]
    
    def stop_all(self):
        """Stop all running scans"""
        if not self.scan_tree.get_children():
            messagebox.showinfo("No Active Scans", "There are no active scans to stop.")
            return
            
        # Ask for confirmation
        if messagebox.askyesno("Confirm Stop", "Are you sure you want to stop all scans?"):
            # Get scan manager
            scan_manager = None
            if self.main_window and hasattr(self.main_window, 'get_scan_manager'):
                scan_manager = self.main_window.get_scan_manager()
                if scan_manager:
                    scan_manager.stop_all_scans()
            
            # Clear UI regardless of scan_manager
            for item in self.scan_tree.get_children():
                self.scan_tree.delete(item)
            
            # Clear scan items dictionary
            self.scan_items.clear()
            
            print("All scans stopped")