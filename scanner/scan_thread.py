# scanner/scan_thread.py
import time
import traceback
from scanner.progress_handler import ProgressHandler
from scanner.excel_manager import ExcelManager

def scan_thread_worker(device_id, device, scanner, wb, sheet, output_file, 
                      scan_params, results_queue, active_scans, get_device_manager):
    """
    Thread thực hiện quét kingdom
    
    Args:
        device_id: ID của thiết bị
        device: Đối tượng thiết bị
        scanner: Đối tượng scanner
        wb: Workbook Excel
        sheet: Sheet Excel
        output_file: Đường dẫn file kết quả
        scan_params: Tham số quét
        results_queue: Queue để gửi kết quả
        active_scans: Dictionary chứa thông tin scan đang hoạt động
        get_device_manager: Hàm lấy device manager
    """
    # Đảm bảo device_id là chuỗi
    device_id = str(device_id)
    
    # Khởi tạo progress handler
    progress_handler = ProgressHandler(results_queue)
    progress_handler.start_tracking()
    
    # Khởi tạo Excel manager
    excel_manager = ExcelManager()
    
    try:
        # Lấy các tham số quét
        kingdom = scan_params['kingdom']
        search_range = scan_params['search_range']
        resume_scanning = scan_params.get('resume_scanning', False)
        
        print(f"Starting scan for kingdom {kingdom} on device {device_id}")
        
        # Điểm bắt đầu
        j = 0
        if resume_scanning:
            j = 4 if isinstance(resume_scanning, int) else 0
        
        # Thông báo bắt đầu quét
        progress_handler.update_progress(
            device_id, 0, search_range, 
            f"Starting scan in kingdom {kingdom}"
        )
        
        # Vòng lặp quét
        for i in range(j, j + search_range):
            # Kiểm tra nếu có yêu cầu dừng
            if device_id in active_scans and active_scans[device_id]["status"] == "stopping":
                print(f"Scanning on device {device_id} was stopped")
                break
                
            try:
                # Cập nhật tiến trình
                progress_handler.update_progress(device_id, i - j + 1, search_range)
                
                # Quét governor
                success = scanner.scan_governor(i, j, sheet, wb, output_file)
                if not success:
                    print(f"Error scanning governor {i-j+1}")
                
                # Lưu định kỳ
                if (i - j + 1) % 5 == 0:
                    excel_manager.save_workbook(wb, output_file)
                    print(f"Saved progress to {output_file}")
                
                # # Swipe để chuyển đến governor tiếp theo nếu không phải governor cuối cùng
                # if i < j + search_range - 1:
                #     device.shell('input swipe 690 540 690 260')
                #     time.sleep(1.2)  # Wait for UI to update
            
            except Exception as e:
                print(f"Error in scan loop at governor {i-j+1}: {e}")
                # Lưu lại tiến trình khi có lỗi
                excel_manager.save_workbook(wb, output_file)
        
        # Kết thúc quét
        excel_manager.save_workbook(wb, output_file)
        
        # Thông báo hoàn thành
        progress_handler.notify_completed(
            device_id, output_file,
            f"Scanning completed for kingdom {kingdom}"
        )
        
        print(f"Scan completed for device {device_id}, kingdom {kingdom}")
        
    except Exception as e:
        print(f"Error in scan thread: {e}")
        traceback.print_exc()
        
        # Thông báo lỗi
        progress_handler.notify_error(device_id, str(e))
    
    finally:
        # Đảm bảo xóa khỏi active_scans và giải phóng thiết bị
        if device_id in active_scans:
            del active_scans[device_id]
        
        # Call the function to get the device manager
        device_manager = get_device_manager()
        if device_manager and hasattr(device_manager, 'mark_device_in_use'):
            device_manager.mark_device_in_use(device_id, False)