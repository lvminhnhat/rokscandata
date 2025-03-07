# scanner/progress_handler.py
import sys
import time

class ProgressHandler:
    def __init__(self, results_queue):
        """
        Khởi tạo đối tượng xử lý tiến trình
        
        Args:
            results_queue: Queue để đưa các cập nhật tiến trình vào
        """
        self.results_queue = results_queue
        self.start_time = None
    
    def start_tracking(self):
        """Bắt đầu theo dõi tiến trình"""
        self.start_time = time.time()
    
    def update_progress(self, device_id, current, total, custom_message=None):
        """
        Cập nhật tiến trình quét
        
        Args:
            device_id: ID của thiết bị đang quét
            current: Vị trí hiện tại
            total: Tổng số lượng cần quét
            custom_message: Thông báo tùy chỉnh (nếu có)
        """
        # Tính toán phần trăm tiến trình
        progress = int((current) * 100 / total)
        
        # Tính toán thời gian còn lại (ETA)
        message = custom_message
        if not message and self.start_time is not None:
            message = self._calculate_eta(current, total)
        
        # In thanh tiến trình trong console
        self.print_progress_bar(current, total)
        
        # Gửi thông báo cập nhật tiến trình
        self.results_queue.put({
            "type": "progress_update",
            "device_id": device_id,
            "progress": progress,
            "message": message or f"Scanning governor {current} of {total}"
        })
    
    def _calculate_eta(self, current, total):
        """Tính toán thời gian còn lại"""
        elapsed_time = time.time() - self.start_time
        
        # Tránh chia cho 0
        if current <= 0:
            return "Calculating..."
        
        avg_time_per_loop = elapsed_time / current
        remaining_loops = total - current
        
        estimated_remaining_time = remaining_loops * avg_time_per_loop
        estimated_minutes = estimated_remaining_time / 60
        
        return f"Scanning governor {current} of {total} ({estimated_minutes:.1f} mins remaining)"
    
    def notify_completed(self, device_id, output_file, message=None):
        """
        Thông báo quét đã hoàn thành
        
        Args:
            device_id: ID của thiết bị
            output_file: Đường dẫn đến file kết quả
            message: Thông báo tùy chỉnh
        """
        self.results_queue.put({
            "type": "scan_completed",
            "device_id": device_id,
            "output_file": output_file,
            "message": message or "Scanning completed"
        })
    
    def notify_error(self, device_id, error):
        """
        Thông báo lỗi trong quá trình quét
        
        Args:
            device_id: ID của thiết bị
            error: Thông báo lỗi
        """
        self.results_queue.put({
            "type": "scan_error",
            "device_id": device_id,
            "error": str(error)
        })
    
    def print_progress_bar(self, iteration, total, bar_length=40):
        """
        In thanh tiến trình vào console
        
        Args:
            iteration: Số lần lặp hiện tại
            total: Tổng số lần lặp
            bar_length: Độ dài của thanh tiến trình
        """
        try:
            progress = iteration / total
            arrow = '=' * int(round(progress * bar_length) - 1) + '>'
            spaces = ' ' * (bar_length - len(arrow))
            
            sys.stdout.write(f'\r[{arrow}{spaces}] {iteration} of {total} ({progress*100:.1f}%)')
            sys.stdout.flush()
        except Exception as e:
            # Xử lý lỗi để tránh crash
            print(f"Error displaying progress bar: {e}")