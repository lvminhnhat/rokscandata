# scanner/scan_manager.py
import threading
import queue
import time
import os
from datetime import datetime

from scanner.excel_manager import ExcelManager
from scanner.scan_thread import scan_thread_worker
from scanner.result_processor import ResultProcessor

class ScanManager:
    def __init__(self, config, device_manager=None):
        """
        Initialize the scan manager
        
        Args:
            config: Application configuration
            device_manager: Optional device manager reference
        """
        self.config = config
        self.device_manager = device_manager
        self.active_scans = {}
        self.results_queue = queue.Queue()
        self.stop_event = threading.Event()
        
        # Tham chiếu đến main window (sẽ được set sau khi khởi tạo)
        self.window = None
        
        # Callback để thông báo cập nhật UI
        self.ui_callback = None
        
        # Khởi tạo result processor
        self.result_processor = ResultProcessor(
            self.results_queue, 
            self.stop_event, 
            self.active_scans,
            self._get_device_manager,
            self.ui_callback
        )
        
        # Start result processing thread
        self.result_thread = threading.Thread(
            target=self.result_processor.process_results_loop, 
            daemon=True
        )
        self.result_thread.start()
    
    def _get_device_manager(self):
        """Tiện ích để lấy device manager từ window"""
        if self.window and hasattr(self.window, 'get_device_manager'):
            return self.window.get_device_manager()
        return self.device_manager
    
    def start_scan(self, device_id, scan_params):
        """
        Start a new scan on the specified device
        
        Args:
            device_id (str): Device identifier
            scan_params (dict): Scan parameters (kingdom, range, etc)
            
        Returns:
            bool: True if scan started successfully, False otherwise
        """
        if str(device_id) in self.active_scans:
            print(f"Scan already running on device {device_id}")
            return False
        
        # Kiểm tra thiết bị có tồn tại không
        device_manager = self._get_device_manager()
        if not device_manager:
            print("Device manager not available")
            return False
            
        # Tạo đối tượng thiết bị thực tế từ device_id
        from Ldplayer.device import Device
        try:
            # Lấy đường dẫn từ config
            ldplayer_path = self.config.ldplayer_path
            device = Device(int(device_id), ldplayer_path)
            
            # Kiểm tra xem thiết bị có hoạt động không
            if not device.is_running():
                print(f"Device {device_id} is not running")
                return False
                
        except Exception as e:
            print(f"Error creating device object: {e}")
            return False
        
        # Đánh dấu thiết bị là đang được sử dụng
        if hasattr(device_manager, 'mark_device_in_use'):
            device_manager.mark_device_in_use(device_id, True)
        
        # Tạo thư mục output nếu cần
        output_dir = os.path.join(self.config.data_dir, 'scan_results')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Tạo file Excel
        excel_manager = ExcelManager()
        wb, sheet = excel_manager.setup_excel(scan_params.get('scan_option', 1))
        output_file = os.path.join(
            output_dir, 
            f"{scan_params['kingdom']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xls"
        )
        
        # Tạo scanner
        from scanner.governor_scanner import GovernorScanner
        scanner = GovernorScanner(device, self.config)
        scanner.set_scan_option(scan_params.get('scan_option', 1))
        
        # Tạo thread cho quá trình quét
        thread = threading.Thread(
            target=scan_thread_worker,
            args=(
                device_id, device, scanner, wb, sheet, output_file,
                scan_params, self.results_queue, self.active_scans,
                self._get_device_manager  # Change this to a function reference
            ),
            daemon=True
        )
        thread.start()
        
        # Lưu thông tin quét đang hoạt động
        self.active_scans[str(device_id)] = {
            "thread": thread,
            "device": device,
            "params": scan_params,
            "start_time": time.time(),
            "progress": 0,
            "output_file": output_file,
            "status": "running"
        }
        
        return True
    
    def stop_scan(self, device_id):
        """
        Stop a running scan
        
        Args:
            device_id: Device identifier
            
        Returns:
            bool: True if scan was stopped, False if no scan running
        """
        device_id = str(device_id)
        if device_id not in self.active_scans:
            return False
        
        # Set status to stopping
        self.active_scans[device_id]["status"] = "stopping"
        
        # Giải phóng thiết bị
        device_manager = self._get_device_manager()
        if device_manager and hasattr(device_manager, 'mark_device_in_use'):
            device_manager.mark_device_in_use(device_id, False)
        
        return True
    
    def stop_all_scans(self):
        """Stop all running scans"""
        for device_id in list(self.active_scans.keys()):
            self.stop_scan(device_id)
    
    def get_active_scans(self):
        """
        Get information about currently running scans
        
        Returns:
            dict: Information about active scans
        """
        return self.active_scans
    
    def set_ui_callback(self, callback):
        """
        Set callback function for UI updates
        
        Args:
            callback: Function to call for UI updates
        """
        self.ui_callback = callback
        self.result_processor.ui_callback = callback
    
    def shutdown(self):
        """Tắt ScanManager an toàn"""
        self.stop_event.set()
        self.stop_all_scans()
        if hasattr(self, 'result_thread') and self.result_thread.is_alive():
            self.result_thread.join(2.0)  # Chờ tối đa 2 giây