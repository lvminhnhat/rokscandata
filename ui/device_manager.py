# ui/device_manager.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import threading

class DeviceManagerFrame(ttk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.devices = []
        self.devices_in_use = set()  # Thêm dòng này
        self.setup_ui()
        self.load_devices()
        
    def setup_ui(self):
        # Main layout
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Device list frame
        list_frame = ttk.Frame(self)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Device list
        columns = ('id', 'name', 'status')
        self.device_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        self.device_tree.heading('id', text='ID')
        self.device_tree.heading('name', text='Name')
        self.device_tree.heading('status', text='Status')
        
        self.device_tree.column('id', width=50)
        self.device_tree.column('name', width=150)
        self.device_tree.column('status', width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.device_tree.yview)
        self.device_tree.configure(yscroll=scrollbar.set)
        
        self.device_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # LDPlayer path
        ldplayer_frame = ttk.LabelFrame(control_frame, text="LDPlayer Path")
        ldplayer_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Initialize default path from config
        ldplayer_path = getattr(self.config, 'ldplayer_path', r"C:\LDPlayer\LDPlayer4.0")
        self.ldplayer_path_var = tk.StringVar(value=ldplayer_path)
        
        # Create path display field
        path_frame = ttk.Frame(ldplayer_frame)
        path_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ldplayer_entry = ttk.Entry(path_frame, textvariable=self.ldplayer_path_var)
        ldplayer_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Browse button
        ttk.Button(path_frame, text="Browse...", command=self.browse_ldplayer).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Save button for path
        ttk.Button(ldplayer_frame, text="Save Path", command=self.save_ldplayer_path).pack(fill=tk.X, padx=5, pady=5)
        
        # Status indicator
        self.path_status_var = tk.StringVar(value="Path not verified")
        ttk.Label(ldplayer_frame, textvariable=self.path_status_var).pack(padx=5, pady=5)
        
        # Device controls
        device_controls = ttk.LabelFrame(control_frame, text="Device Controls")
        device_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(device_controls, text="Refresh List", command=self.refresh_devices).pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(device_controls, text="Start Selected", command=self.start_selected).pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(device_controls, text="Stop Selected", command=self.stop_selected).pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(device_controls, text="Start All", command=self.start_all).pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(device_controls, text="Stop All", command=self.stop_all).pack(fill=tk.X, padx=5, pady=5)
    
    def browse_ldplayer(self):
        """Open file dialog to select LDPlayer path"""
        # Ask for directory rather than file
        ldplayer_dir = filedialog.askdirectory(
            title="Select LDPlayer Directory",
            initialdir=os.path.dirname(self.ldplayer_path_var.get())
        )
        
        # Check if user canceled the dialog
        if ldplayer_dir:
            # Check if it's a valid LDPlayer directory (has ldconsole.exe)
            if os.path.isfile(os.path.join(ldplayer_dir, 'ldconsole.exe')):
                self.ldplayer_path_var.set(ldplayer_dir)
                self.path_status_var.set("Valid LDPlayer path")
                # Update config immediately
                self.save_ldplayer_path()
            else:
                # Look for ldconsole.exe in subdirectories
                for root, dirs, files in os.walk(ldplayer_dir):
                    if 'ldconsole.exe' in files:
                        self.ldplayer_path_var.set(root)
                        self.path_status_var.set("Valid LDPlayer path found in subdirectory")
                        # Update config immediately
                        self.save_ldplayer_path()
                        return
                
                # Not found
                messagebox.showerror(
                    "Invalid Directory", 
                    "The selected directory does not appear to be a valid LDPlayer installation. "
                    "Please select a directory containing ldconsole.exe."
                )
                self.path_status_var.set("Invalid LDPlayer path")
    
    def save_ldplayer_path(self):
        """Save LDPlayer path to configuration"""
        path = self.ldplayer_path_var.get()
        
        # Basic validation
        if not path or not os.path.exists(path):
            messagebox.showerror("Invalid Path", "The specified path does not exist.")
            return
        
        # Look for ldconsole.exe
        ldconsole_path = os.path.join(path, 'ldconsole.exe')
        if not os.path.isfile(ldconsole_path):
            messagebox.showerror(
                "Invalid Path", 
                "ldconsole.exe not found in the specified path.\n"
                "Please select the correct LDPlayer directory."
            )
            return
            
        # Update config
        try:
            # Update the configuration attribute
            self.config.ldplayer_path = path
            
            # Save config to file if there's a save_config method
            from utils.config_manager import save_config
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'config',
                'config.json'
            )
            save_config(self.config, config_path)
            
            self.path_status_var.set("Path saved successfully")
            messagebox.showinfo("Success", "LDPlayer path saved successfully.")
            
            # Refresh device list with new path
            self.refresh_devices()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save LDPlayer path: {str(e)}")
    
    def refresh_devices(self):
        """Update the device list with currently available devices"""
        try:
            # Clear the existing list
            self.device_tree.delete(*self.device_tree.get_children())
            
            # Get the LDPlayer path
            ldplayer_path = self.ldplayer_path_var.get()
            if not ldplayer_path or not os.path.exists(ldplayer_path):
                messagebox.showerror("Error", "Please set a valid LDPlayer path first.")
                return
            
            # Use subprocess to run ldconsole list2 command
            import subprocess
            ldconsole_path = os.path.join(ldplayer_path, 'ldconsole.exe')
            
            # Check if ldconsole.exe exists
            if not os.path.isfile(ldconsole_path):
                messagebox.showerror("Error", "ldconsole.exe not found. Please check the LDPlayer path.")
                return
                
            try:
                # Run ldconsole list2 to get device list
                result = subprocess.run(
                    [ldconsole_path, 'list2'], 
                    capture_output=True, 
                    text=True, 
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                # Parse output
                if result.returncode == 0:
                    devices = result.stdout.strip().split('\n')
                    for device in devices:
                        if device.strip():
                            # Format: index,name,top_window_handle,bind_window_handle,pid
                            parts = device.split(',')
                            if len(parts) >= 3:
                                device_id = parts[0]
                                device_name = parts[1]
                                running = int(parts[2]) > 0  # If handle > 0, it's running
                                
                                # Xác định trạng thái
                                status = "Stopped"
                                if running:
                                    if device_id in self.devices_in_use:
                                        status = "In Use"
                                    else:
                                        status = "Running"
                                
                                self.device_tree.insert(
                                    '', 'end', 
                                    values=(device_id, device_name, status)
                                )
                else:
                    # Try alternative command if list2 not supported
                    result = subprocess.run(
                        [ldconsole_path, 'list'], 
                        capture_output=True, 
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    devices = result.stdout.strip().split('\n')
                    for device in devices:
                        if device.strip():
                            # Format differs in older versions
                            parts = device.split(',')
                            if len(parts) >= 2:
                                device_id = parts[0]
                                device_name = parts[1]
                                
                                # Check if it's running (simplified)
                                try:
                                    is_running_result = subprocess.run(
                                        [ldconsole_path, 'isrunning', '--index', device_id],
                                        capture_output=True,
                                        text=True,
                                        creationflags=subprocess.CREATE_NO_WINDOW
                                    )
                                    running = "running" in is_running_result.stdout.lower()
                                except:
                                    running = False
                                    
                                # Xác định trạng thái
                                status = "Stopped"
                                if running:
                                    if device_id in self.devices_in_use:
                                        status = "In Use"
                                    else:
                                        status = "Running"
                                
                                self.device_tree.insert(
                                    '', 'end', 
                                    values=(device_id, device_name, status)
                                )
            except Exception as e:
                # Fallback to mock data if commands fail
                print(f"Error running ldconsole: {e}")
                for i in range(3):  # Add mock devices
                    self.device_tree.insert('', 'end', values=(i, f"LDPlayer-{i}", "Stopped"))
                    
            # Update device count
            device_count = len(self.device_tree.get_children())
            messagebox.showinfo("Devices Refreshed", f"Found {device_count} LDPlayer devices.")
                    
        except Exception as e:
            print(f"Error refreshing devices: {e}")
            messagebox.showerror("Error", f"Failed to refresh devices: {str(e)}")
            
            # Fallback to mock data
            for i in range(3):  # Add mock devices
                self.device_tree.insert('', 'end', values=(i, f"LDPlayer-{i}", "Stopped"))
    
    def start_selected(self):
        """Start selected LDPlayer instances"""
        selected_items = self.device_tree.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select a device to start")
            return
        
        ldplayer_path = self.ldplayer_path_var.get()
        if not ldplayer_path or not os.path.exists(ldplayer_path):
            messagebox.showerror("Error", "Please set a valid LDPlayer path first.")
            return
            
        ldconsole_path = os.path.join(ldplayer_path, 'ldconsole.exe')
        if not os.path.isfile(ldconsole_path):
            messagebox.showerror("Error", "ldconsole.exe not found. Please check the LDPlayer path.")
            return
        
        # Start each selected device
        import subprocess
        for item in selected_items:
            device_id = self.device_tree.item(item, 'values')[0]
            try:
                subprocess.Popen(
                    [ldconsole_path, 'launch', '--index', str(device_id)],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                print(f"Starting device {device_id}")
                # Update status in tree
                self.device_tree.item(item, values=(device_id, self.device_tree.item(item, 'values')[1], "Starting..."))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start device {device_id}: {str(e)}")
        
        # Schedule a refresh after a delay to update statuses
        self.after(5000, self.refresh_devices)
    
    def stop_selected(self):
        """Stop selected LDPlayer instances"""
        selected_items = self.device_tree.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select a device to stop")
            return
        
        ldplayer_path = self.ldplayer_path_var.get()
        if not ldplayer_path or not os.path.exists(ldplayer_path):
            messagebox.showerror("Error", "Please set a valid LDPlayer path first.")
            return
            
        ldconsole_path = os.path.join(ldplayer_path, 'ldconsole.exe')
        if not os.path.isfile(ldconsole_path):
            messagebox.showerror("Error", "ldconsole.exe not found. Please check the LDPlayer path.")
            return
        
        # Stop each selected device
        import subprocess
        for item in selected_items:
            device_id = self.device_tree.item(item, 'values')[0]
            try:
                subprocess.Popen(
                    [ldconsole_path, 'quit', '--index', str(device_id)],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                print(f"Stopping device {device_id}")
                # Update status in tree
                self.device_tree.item(item, values=(device_id, self.device_tree.item(item, 'values')[1], "Stopping..."))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to stop device {device_id}: {str(e)}")
        
        # Schedule a refresh after a delay to update statuses
        self.after(5000, self.refresh_devices)
    
    def start_all(self):
        """Start all LDPlayer instances"""
        if not self.device_tree.get_children():
            messagebox.showinfo("No Devices", "No devices found. Please refresh the device list.")
            return
            
        if messagebox.askyesno("Confirm Start All", "Are you sure you want to start all devices? This may take significant system resources."):
            for item in self.device_tree.get_children():
                self.device_tree.selection_add(item)
            self.start_selected()
    
    def stop_all(self):
        """Stop all LDPlayer instances"""
        if not self.device_tree.get_children():
            messagebox.showinfo("No Devices", "No devices found.")
            return
            
        if messagebox.askyesno("Confirm Stop All", "Are you sure you want to stop all devices?"):
            for item in self.device_tree.get_children():
                self.device_tree.selection_add(item)
            self.stop_selected()
    
    def load_devices(self):
        """Load saved devices from config and refresh the actual device list"""
        try:
            # Load saved device configurations if file exists
            if hasattr(self.config, 'devices_file') and os.path.exists(self.config.devices_file):
                with open(self.config.devices_file, 'r') as f:
                    self.devices = json.load(f)
            
            # Also refresh the actual device list from LDPlayer
            self.after(500, self.refresh_devices)  # Small delay to ensure UI is fully loaded
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load devices: {e}")
    
    def save_devices(self):
        try:
            os.makedirs(os.path.dirname(self.config.devices_file), exist_ok=True)
            with open(self.config.devices_file, 'w') as f:
                json.dump(self.devices, f, indent=2)
            messagebox.showinfo("Success", "Devices saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save devices: {e}")
    
    def refresh_device_list(self):
        self.device_tree.delete(*self.device_tree.get_children())
        for device in self.devices:
            self.device_tree.insert('', 'end', values=(device['id'], device['name'], "Stopped"))
    
    def add_device(self):
        # Implementation of add device dialog
        pass
    
    def edit_device(self):
        # Implementation of edit device dialog
        pass
    
    def remove_device(self):
        # Implementation of remove device
        pass

    def mark_device_in_use(self, device_id, in_use=True):
        """
        Đánh dấu thiết bị là đang được sử dụng (hoặc không)
        
        Args:
            device_id: ID của thiết bị
            in_use: True nếu đang sử dụng, False nếu không
            
        Returns:
            bool: True nếu thành công, False nếu không tìm thấy thiết bị
        """
        device_id = str(device_id)
        device_found = False
        
        # Cập nhật trong UI
        for item in self.device_tree.get_children():
            values = self.device_tree.item(item, 'values')
            if str(values[0]) == device_id:
                device_found = True
                status = "In Use" if in_use else "Running"
                self.device_tree.item(item, values=(values[0], values[1], status))
                break
        
        # Cập nhật tập hợp theo dõi
        if in_use:
            self.devices_in_use.add(device_id)
        else:
            self.devices_in_use.discard(device_id)
        
        return device_found

    def get_available_devices(self):
        """
        Lấy danh sách các thiết bị khả dụng (đang chạy và không được sử dụng)
        
        Returns:
            list: Danh sách các thiết bị khả dụng
        """
        available_devices = []
        
        for item in self.device_tree.get_children():
            values = self.device_tree.item(item, 'values')
            device_id = str(values[0])
            device_name = values[1]
            status = values[2]
            
            # Thiết bị đang chạy và không trong danh sách đang sử dụng
            if status == "Running" and device_id not in self.devices_in_use:
                available_devices.append({
                    'id': device_id,
                    'name': device_name,
                    'status': "Available"
                })
        
        return available_devices