# scanner/result_processor.py
import queue

class ResultProcessor:
    def __init__(self, results_queue, stop_event, active_scans, get_device_manager, ui_callback=None):
        """
        Khởi tạo đối tượng xử lý kết quả
        
        Args:
            results_queue: Queue chứa kết quả
            stop_event: Event để dừng thread
            active_scans: Dictionary chứa thông tin scan đang hoạt động
            get_device_manager: Hàm lấy device manager
            ui_callback: Callback cập nhật UI
        """
        self.results_queue = results_queue
        self.stop_event = stop_event
        self.active_scans = active_scans
        self.get_device_manager = get_device_manager
        self.ui_callback = ui_callback
    
    def process_results_loop(self):
        """Vòng lặp xử lý kết quả từ queue"""
        while not self.stop_event.is_set():
            try:
                # Lấy kết quả tiếp theo với timeout
                try:
                    result = self.results_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                    
                device_id = result.get("device_id")
                result_type = result.get("type")
                
                # Xử lý result dựa vào type
                if result_type == "progress_update" and device_id in self.active_scans:
                    self._handle_progress_update(result, device_id)
                elif result_type == "scan_completed" and device_id in self.active_scans:
                    self._handle_scan_completed(result, device_id)
                elif result_type == "scan_error" and device_id in self.active_scans:
                    self._handle_scan_error(result, device_id)
                
                self.results_queue.task_done()
                
            except Exception as e:
                print(f"Error processing results: {e}")
    
    def _handle_progress_update(self, result, device_id):
        """Xử lý cập nhật tiến trình"""
        progress = result.get("progress", 0)
        self.active_scans[device_id]["progress"] = progress
        
        # Thông báo cập nhật UI nếu có callback
        if self.ui_callback:
            self.ui_callback("progress_update", {
                "device_id": device_id,
                "progress": progress,
                "message": result.get("message", "")
            })
    
    def _handle_scan_completed(self, result, device_id):
        """Xử lý khi hoàn thành quét"""
        output_file = result.get("output_file", "")
        
        # Thông báo UI nếu có callback
        if self.ui_callback:
            self.ui_callback("scan_completed", {
                "device_id": device_id,
                "output_file": output_file,
                "message": result.get("message", "")
            })
        
        # Giải phóng thiết bị
        self._release_device(device_id)
        
        # Xóa khỏi active scans
        if device_id in self.active_scans:
            del self.active_scans[device_id]
    
    def _handle_scan_error(self, result, device_id):
        """Xử lý khi có lỗi"""
        error = result.get("error", "Unknown error")
        
        # Thông báo UI nếu có callback
        if self.ui_callback:
            self.ui_callback("scan_error", {
                "device_id": device_id,
                "error": error
            })
        
        # Giải phóng thiết bị
        self._release_device(device_id)
        
        # Xóa khỏi active scans
        if device_id in self.active_scans:
            del self.active_scans[device_id]
    
    def _release_device(self, device_id):
        """Giải phóng thiết bị"""
        device_manager = self.get_device_manager()
        if device_manager and hasattr(device_manager, 'mark_device_in_use'):
            device_manager.mark_device_in_use(device_id, False)