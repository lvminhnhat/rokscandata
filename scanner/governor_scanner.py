import os
import time
import cv2
import numpy as np
import pytesseract
import tkinter as tk
import random
import threading
from datetime import date

class GovernorScanner:
    def __init__(self, device, config):
        """
        Initialize the governor scanner
        
        Args:
            device: The device to use for scanning
            config: Application configuration
        """
        self.device = device

        self.config = config
        # Configure pytesseract
        pytesseract.pytesseract.tesseract_cmd = config.tesseract_path
        # Y positions for governors in the list
        self.Y = [285, 390, 490, 590, 605]
        # Set default scan option
        self.scan_option = getattr(config, 'scan_option', 1)
        
    def set_scan_option(self, scan_option):
        """
        Set scan option
        1 = full scan
        2 = power + kill points only 
        3 = power + kill points + dead
        """
        self.scan_option = scan_option
        
    def randomize_time(self, base_time):
        """
        Tạo một thời gian ngẫu nhiên gần base_time và chờ
        
        Args:
            base_time: Thời gian cơ bản tính bằng giây
        """
        try:
            import random
            variation = random.uniform(-0.1, 0.1) * base_time
            sleep_time = base_time + variation
            if sleep_time < 0.1:
                sleep_time = 0.1  # Đảm bảo thời gian ngủ tối thiểu
            time.sleep(sleep_time)
        except Exception as e:
            print(f"Error in randomize_time: {e}")
            # Fallback to regular sleep
            time.sleep(base_time)
    
    def capture_image(self, filename):
        """
        Chụp ảnh màn hình từ thiết bị
        
        Args:
            filename: Tên file để lưu
            
        Returns:
            str: Đường dẫn đến file ảnh
        """
        try:
            # Đảm bảo rằng thư mục screenshots tồn tại
            screenshots_dir = getattr(self.config, 'screenshots_dir', 'screenshots')

            
            # Xử lý đường dẫn tương đối/tuyệt đối
            if not os.path.isabs(screenshots_dir):
                # Nếu là đường dẫn tương đối, lấy từ thư mục gốc dự án
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                screenshots_dir = os.path.join(base_dir, screenshots_dir)
            
            # Đảm bảo thư mục tồn tại
            if not os.path.exists(screenshots_dir):
                os.makedirs(screenshots_dir)
            
            # Tạo đường dẫn đầy đủ với timestamp để tránh trùng lặp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            base_filename, ext = os.path.splitext(filename)
            if not ext:
                ext = ".png"
            safe_filename = f"{base_filename}_{timestamp}{ext}"
            output_path = os.path.join(screenshots_dir, safe_filename)
            
            # Chụp ảnh với tối đa 3 lần thử
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                success = self.device.screencap(output_path)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                    return output_path
                
                print(f"Screenshot attempt {attempt}/{max_attempts} failed. Retrying...")
                time.sleep(1)  # Chờ một chút trước khi thử lại
            
            # Nếu tất cả các lần thử đều thất bại, tạo ảnh trống
            print(f"Failed to capture screenshot after {max_attempts} attempts. Creating empty image.")
            try:
                # Tạo ảnh PNG trống cơ bản (1x1 pixel)
                with open(output_path, 'wb') as f:
                    # Đây là dữ liệu nhị phân của một ảnh PNG 1x1 pixel đơn giản
                    f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n\x86\xb0\x00\x00\x00\x00IEND\xaeB`\x82')
                return output_path
            except Exception as e:
                print(f"Error creating empty image: {e}")
                return None
        except Exception as e:
            print(f"Error in capture_image: {e}")
            return None
        
    def get_clip_board(self):
        # Khởi tạo biến static cho lớp nếu chưa tồn tại
        if not hasattr(GovernorScanner, '_clipboard_lock'):
            GovernorScanner._clipboard_lock = threading.RLock()
        
        # Thử lấy khóa với timeout
        max_attempts = 10
        for attempt in range(max_attempts):
            if GovernorScanner._clipboard_lock.acquire(blocking=False):
                try:
                    # Có quyền truy cập clipboard
                    retry_attempts = 5
                    for clipboard_attempt in range(retry_attempts):
                        try:
                            import tkinter as tk
                            root = tk.Tk()
                            root.withdraw()  # Ẩn cửa sổ Tkinter
                            data = root.clipboard_get()
                            root.destroy()
                            return data
                        except tk.TclError:
                            print(f"Không thể truy cập clipboard, thử lại lần {clipboard_attempt+1}/{retry_attempts}...")
                            time.sleep(0.5)  # Đợi 0.5 giây trước khi thử lại
                        except Exception as e:
                            print(f"Lỗi khi truy cập clipboard: {e}")
                            break
                    
                    print("Không thể truy cập clipboard sau nhiều lần thử.")
                    return "Null"
                finally:
                    # Đảm bảo luôn giải phóng khóa sau khi dùng xong
                    GovernorScanner._clipboard_lock.release()
        else:
            # Không có quyền, đợi một chút và thử lại
            print(f"Đang chờ quyền truy cập clipboard (lần {attempt+1}/{max_attempts})...")
            time.sleep(1)
    
        print("Không thể lấy quyền truy cập clipboard sau nhiều lần thử.")
        return "Null"
    
    def preprocess_image(self, filename, roi):
        """
        Tiền xử lý ảnh cho OCR
        
        Args:
            filename: Đường dẫn đến file ảnh
            roi: Tuple (x, y, w, h) chỉ định vùng quan tâm
        
        Returns:
            numpy.ndarray: Ảnh đã tiền xử lý hoặc None nếu xử lý thất bại
        """
        # Kiểm tra xem đường dẫn có tồn tại không
        if filename is None or not os.path.exists(filename):
            print(f"Image file does not exist: {filename}")
            return None
        
        try:
            # Đọc ảnh
            img = cv2.imread(filename)
            if img is None:
                print(f"Failed to load image: {filename}")
                return None
            
            # Kiểm tra xem roi có hợp lệ không
            x, y, w, h = roi
            if x < 0 or y < 0 or w <= 0 or h <= 0:
                print(f"Invalid ROI: {roi}")
                return None
            
            # Kiểm tra xem roi có nằm trong ảnh không
            height, width = img.shape[:2]
            if x >= width or y >= height:
                print(f"ROI outside image bounds: {roi}, image size: {width}x{height}")
                return None
            
            # Điều chỉnh roi nếu nó vượt quá ranh giới ảnh
            if x + w > width:
                w = width - x
            if y + h > height:
                h = height - y
            
            # Cắt ảnh theo roi
            try:
                cropped = img[y:y+h, x:x+w]
            except Exception as e:
                print(f"Error cropping image: {e}")
                return None
            
            # Chuyển đổi sang ảnh xám
            try:
                gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
            except Exception as e:
                print(f"Error converting to grayscale: {e}")
                return None
            
            # Áp dụng ngưỡng
            try:
                _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                return binary
            except Exception as e:
                print(f"Error applying threshold: {e}")
                return None
            
        except Exception as e:
            print(f"Error in preprocess_image: {e}")
            return None
    
    def preprocess_image2(self, filename, roi):
        """
        Tiền xử lý ảnh cho OCR
        
        Args:
            filename: Đường dẫn đến file ảnh
            roi: (x, y, w, h) vùng cần xử lý
            
        Returns:
            numpy.ndarray: Ảnh đã xử lý
        """
        try:
            img = cv2.imread(filename)
            if img is None:
                print(f"Failed to load image: {filename}")
                return None
                
            x, y, w, h = roi
            cropped = img[y:y+h, x:x+w]
            gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            return binary
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return None
    
    def read_ocr_from_image(self, image, config=""):
        """
        Đọc text từ ảnh sử dụng OCR
        
        Args:
            image: Ảnh đã tiền xử lý
            config: Cấu hình cho Tesseract
            
        Returns:
            str: Text nhận diện được
        """
        if image is None:
            return ""
            
        try:
            text = pytesseract.image_to_string(image, config=config)
            return text.strip()
        except Exception as e:
            print(f"OCR error: {e}")
            return ""
    
    
    def scan_governor(self, i, j, sheet, wb, output_file):
        """
        Quét thông tin governor và lưu vào Excel
        
        Args:
            i: Chỉ số của governor
            j: Chỉ số bắt đầu (cho phân trang)
            sheet: Excel sheet
            wb: Excel workbook
            output_file: File đầu ra
            
        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        try:
            # Tính toán vị trí dựa trên chỉ số
            k = min(i, len(self.Y) - 1)
            print(f"Scanning governor {i-j} at Y={self.Y[k]}")
            
            # Tap vào governor
            self.device.shell(f'input tap 690 {self.Y[k]}')
            self.randomize_time(1.3)
            
            # Đảm bảo tab thông tin đã mở đúng cách
            check_info_opened = False
            for attempt in range(5):
                # Chụp màn hình để kiểm tra
                screenshot_path = self.capture_image(f"{self.device.id}/gov_{i-j}_check.png")
                
                # Kiểm tra xem profile đã mở chưa bằng cách tìm nút "More Info"
                check_more_info_img = self.preprocess_image2(screenshot_path, (170, 775, 116, 29))
                if check_more_info_img is not None:
                    check_text = self.read_ocr_from_image(check_more_info_img)
                    if 'MoreInfo' in check_text or 'Info' in check_text:
                        check_info_opened = True
                        break
                
                # Nếu chưa mở, thử lại
                self.device.shell(f'input swipe 690 605 690 540')
                time.sleep(0.5)
                self.device.shell(f'input tap 690 {self.Y[k]}')
                self.randomize_time(1.2)
            
            if not check_info_opened:
                print(f"Warning: Could not verify governor profile opened for governor {i-j}")
            
            # Dựa vào scan_option để thực hiện loại quét tương ứng
            if self.scan_option == 2:
                success = self.scan_governor_basic(i, j, sheet, screenshot_path)
            elif self.scan_option == 3:
                success = self.scan_governor_pkd(i, j, sheet,screenshot_path)
            else:
                success = self.scan_governor_full(i, j, sheet,screenshot_path)
            
            # Đảm bảo đóng governor info
            self.device.shell('input tap 1453 88')
            time.sleep(0.8)
            
            # Lưu workbook định kỳ
            if i % 5 == 0:
                try:
                    wb.save(output_file)
                    print(f"Progress saved to {output_file}")
                except Exception as e:
                    print(f"Error saving workbook: {e}")
            
            return success
        except Exception as e:
            print(f"Error scanning governor: {e}")
            # Đảm bảo đóng governor info ngay cả khi có lỗi
            try:
                self.device.shell('input tap 1453 88')
            except:
                pass
            return False
    
    def scan_governor_basic(self, i, j, sheet, screenshot_path):
        """
        Scan governor with basic info (name, ID, power, kill points)
        
        Args:
            i: Governor index
            j: Start index (for pagination)
            sheet: Excel sheet
            
        Returns:
            bool: Success or failure
        """
        try:
            
            
            # Get governor name
            gov_name_img = self.preprocess_image(screenshot_path, (398, 177, 280, 38))
            gov_name = self.read_ocr_from_image(gov_name_img)
            
            # Get governor ID
            gov_id_img = self.preprocess_image(screenshot_path, (402, 221, 134, 34))
            gov_id = self.read_ocr_from_image(gov_id_img, "--psm 7 -c tessedit_char_whitelist=0123456789")
            
            # Get power
            gov_power_img = self.preprocess_image(screenshot_path, (636, 221, 164, 34))
            gov_power = self.read_ocr_from_image(gov_power_img, "--psm 7 -c tessedit_char_whitelist=0123456789,")
            
            # Get kill points
            gov_kp_img = self.preprocess_image(screenshot_path, (415, 267, 170, 38))
            gov_killpoints = self.read_ocr_from_image(gov_kp_img, "--psm 7 -c tessedit_char_whitelist=0123456789,")
            
            # Print info for debugging
            self._print_governor_info_basic(gov_id, gov_name, gov_power, gov_killpoints)
            
            # Write to Excel
            self._write_basic_data(sheet, i, j, gov_name, gov_id, gov_power, gov_killpoints)
            
            return True
        except Exception as e:
            print(f"Error in scan_governor_basic: {e}")
            return False
    
    def scan_governor_pkd(self, i, j, sheet, screenshot_path):
        """
        Scan governor with power, kill points, and dead troops
        
        Args:
            i: Governor index
            j: Start index (for pagination)
            sheet: Excel sheet
            
        Returns:
            bool: Success or failure
        """
        try:
            
            # Get governor name
            gov_name_img = self.preprocess_image(screenshot_path, (398, 177, 280, 38))
            gov_name = self.read_ocr_from_image(gov_name_img)
            
            # Get governor ID
            gov_id_img = self.preprocess_image(screenshot_path, (402, 221, 134, 34))
            gov_id = self.read_ocr_from_image(gov_id_img, "--psm 7 -c tessedit_char_whitelist=0123456789")
            
            # Get power
            gov_power_img = self.preprocess_image(screenshot_path, (636, 221, 164, 34))
            gov_power = self.read_ocr_from_image(gov_power_img, "--psm 7 -c tessedit_char_whitelist=0123456789,")
            
            # Get kill points
            gov_kp_img = self.preprocess_image(screenshot_path, (415, 267, 170, 38))
            gov_killpoints = self.read_ocr_from_image(gov_kp_img, "--psm 7 -c tessedit_char_whitelist=0123456789,")
            
            # Swipe để xem more info
            self.device.shell('input swipe 690 500 690 300')
            self.randomize_time(1.0)
            
            # Chụp màn hình thứ hai
            screenshot_path2 = self.capture_image(f"gov_{i-j}_pkd2.png")
            
            # Get dead troops
            gov_dead_img = self.preprocess_image(screenshot_path2, (415, 267, 170, 38))
            gov_dead = self.read_ocr_from_image(gov_dead_img, "--psm 7 -c tessedit_char_whitelist=0123456789,")
            
            # Print info for debugging
            self._print_governor_info_pkd(gov_id, gov_name, gov_power, gov_killpoints, gov_dead)
            
            # Write to Excel
            self._write_pkd_data(sheet, i, j, gov_name, gov_id, gov_power, gov_killpoints, gov_dead)
            
            return True
        except Exception as e:
            print(f"Error in scan_governor_pkd: {e}")
            return False
    
    def match_template(self, image, template, method=cv2.TM_CCOEFF_NORMED):
        """
        Tìm vị trí template trong ảnh
        
        Args:
            image: Ảnh nguồn
            template: Mẫu cần tìm
            method: Phương pháp so khớp
            
        Returns:
            tuple: (vị trí trung tâm, điểm khớp tốt nhất)
        """
        try:
            # Thực hiện template matching
            result = cv2.matchTemplate(image, template, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # Chọn kết quả tốt nhất dựa vào phương pháp
            if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                best_match_loc = min_loc
                score = min_val
            else:
                best_match_loc = max_loc
                score = max_val
                
            # Trả về vị trí trung tâm và độ tin cậy
            center_x = best_match_loc[0] + template.shape[1] // 2
            center_y = best_match_loc[1] + template.shape[0] // 2
            return (center_x, center_y), score
        except Exception as e:
            print(f"Error in match_template: {e}")
            return None, None
    
    def preprocess_image3(self, filename, roi):
        """
        Tiền xử lý ảnh với phương pháp nâng cao cho OCR
        (Hữu ích cho văn bản khó đọc)
        
        Args:
            filename: Đường dẫn đến file ảnh
            roi: Tuple (x, y, w, h) chỉ định vùng quan tâm
        
        Returns:
            numpy.ndarray: Ảnh đã tiền xử lý hoặc None nếu xử lý thất bại
        """
        if filename is None or not os.path.exists(filename):
            print(f"Image file does not exist: {filename}")
            return None
        
        try:
            # Đọc ảnh
            img = cv2.imread(filename)
            if img is None:
                print(f"Failed to load image: {filename}")
                return None
                
            # Cắt ảnh theo roi
            x, y, w, h = roi
            cropped = img[y:y+h, x:x+w]
            
            # Chuyển đổi sang ảnh xám
            gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
            
            # Áp dụng lọc trung vị để giảm nhiễu
            gray = cv2.medianBlur(gray, 3)
            
            # Áp dụng ngưỡng ngược để tối ưu cho văn bản
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            return binary
        except Exception as e:
            print(f"Error in preprocess_image3: {e}")
            return None
    def copy_name(self):
        
        self.device.shell('input tap 538 178')  # Vị trí để copy tên
        time.sleep(0.8)
        gov_name_clip = self.get_clip_board()
        return gov_name_clip
            
    def scan_governor_full(self, i, j, sheet, main_img):
        """
        Quét đầy đủ thông tin của governor dựa trên logic của scan.py
        
        Args:
            i: Governor index
            j: Start index (for pagination)
            sheet: Excel sheet
            
        Returns:
            bool: Success or failure
        """
        try:
            # Các biến để lưu thông tin
            gov_name = "Unknown"
            gov_id = "0"
            gov_power = "0"
            gov_killpoints = "0"
            gov_dead = "0"
            kills_tiers = ["0", "0", "0", "0", "0"]  # T1, T2, T3, T4, T5
            gov_rss_assistance = "0"
            gov_alliance_helps = "0"
            alliance_tag = "Unknown"
            gov_kills_high = "0"  # KvK high kills
            gov_deads_high = "0"  # KvK high deads
            gov_sevs_high = "0"   # KvK severely wounded
            
            if not main_img:
                print(f"Failed to capture main screenshot for governor {i-j}")
                return False
            
            try:  
                # lấy id của governor
                gov_id_img = self.preprocess_image2(main_img, (720, 176, 200, 34))
                if gov_id_img is not None:
                    gov_id_text = self.read_ocr_from_image(gov_id_img, "--psm 7 -c tessedit_char_whitelist=0123456789")
                    if gov_id_text:
                        gov_id = gov_id_text
            except Exception as e:
                print(f"Error getting governor ID: {e}")
            
            # Lấy tên governor (thử copy từ clipboard)
            try:
                self.device.shell('input tap 654 228')  # Vị trí để copy tên
                time.sleep(0.3)
                gov_name_clip = self.get_clip_board()
                if gov_name_clip and gov_name_clip != "Null":
                    gov_name = gov_name_clip
                else:
                    # Thử đọc từ ảnh nếu clipboard không hoạt động
                    gov_name_img = self.preprocess_image(main_img, (398, 177, 280, 38))
                    if gov_name_img is not None:
                        gov_name_text = self.read_ocr_from_image(gov_name_img)
                        if gov_name_text:
                            gov_name = gov_name_text
            except Exception as e:
                print(f"Error getting governor name: {e}")
            
            # Tap vào Stats để xem các thông tin chi tiết hơn
            self.device.shell('input tap 1226 486')  # Vị trí nút KvK Stats
            self.randomize_time(0.8)
            
            # Chụp màn hình KvK stats
            kvk_img = self.capture_image(f"{self.device.id}/gov_{i-j}_kvk.png")
            
            # Đọc Power và Kill Points từ màn hình KvK stats
            if kvk_img:
                try:
                    gov_power_img = self.preprocess_image2(main_img, (856, 320, 240, 40))
                    if gov_power_img is not None:
                        gov_power_text = self.read_ocr_from_image(gov_power_img, "--psm 6 -c tessedit_char_whitelist=0123456789")
                        if gov_power_text:
                            gov_power = gov_power_text
                    
                    gov_killpoints_img = self.preprocess_image2(main_img, (1120, 320, 280, 40))
                    if gov_killpoints_img is not None:
                        gov_kp_text = self.read_ocr_from_image(gov_killpoints_img, "-c tessedit_char_whitelist=0123456789")
                        if gov_kp_text:
                            gov_killpoints = gov_kp_text
                            
                    # Alliance tag
                    alliance_tag_img = self.preprocess_image(main_img, (580, 320, 250, 40))
                    if alliance_tag_img is not None:
                        alliance_tag_text = self.read_ocr_from_image(alliance_tag_img)
                        if alliance_tag_text:
                            alliance_tag = alliance_tag_text
                    
                    # KvK Stats        
                    gov_kills_high_img = self.preprocess_image(kvk_img, (1000, 380, 180, 50))
                    if gov_kills_high_img is not None:
                        kills_high_text = self.read_ocr_from_image(gov_kills_high_img, "--psm 6 -c tessedit_char_whitelist=0123456789")
                        if kills_high_text:
                            gov_kills_high = kills_high_text
                    
                    gov_deads_high_img = self.preprocess_image(kvk_img, (1020, 460, 200, 35))
                    if gov_deads_high_img is not None:
                        deads_high_text = self.read_ocr_from_image(gov_deads_high_img, "-c tessedit_char_whitelist=0123456789")
                        if deads_high_text:
                            gov_deads_high = deads_high_text
                    
                    # Tap vào tab Season để xem Severely Wounded
                    for _ in range(2):
                        self.randomize_time(0.6)
                        self.device.shell('input tap 1174 304')
                    
                    self.randomize_time(0.5)
                    # Chụp ảnh màn hình kills tier
                    kills_img = self.capture_image(f"{self.device.id}/gov_{i-j}_kills.png")
                    
                    if kvk_img:
                        gov_sevs_high_img = self.preprocess_image(kvk_img, (1020, 510, 200, 35))
                        if gov_sevs_high_img is not None:
                            sevs_high_text = self.read_ocr_from_image(gov_sevs_high_img, "-c tessedit_char_whitelist=0123456789")
                            if sevs_high_text:
                                gov_sevs_high = sevs_high_text
                except Exception as e:
                    print(f"Error reading KvK stats: {e}")
            
            # Chuyển đến tab Kills/Deads để xem các thông tin tiers
            self.device.shell('input tap 226 724')  # Tab Kills/Deads
            self.randomize_time(0.8)
            
            
            # Đọc thông tin các tier kills
            if kills_img:
                try:
                    # Đọc các tier kills
                    for idx, y in enumerate(range(420, 620, 45)):
                        if idx >= 5:  # Chỉ đọc 5 tier
                            break
                            
                        tier_img = self.preprocess_image(kills_img, (916, y, 215, 26))
                        if tier_img is not None:
                            tier_text = self.read_ocr_from_image(tier_img, "--psm 6 -c tessedit_char_whitelist=0123456789")
                            if tier_text:
                                kills_tiers[idx] = tier_text
                except Exception as e:
                    print(f"Error reading kills tiers: {e}")
            
            # Chuyển đến More Info để xem thông tin deaths và rss assistance
            self.randomize_time(0.3)
            more_img = self.capture_image(f"{self.device.id}/gov_{i-j}_more.png")
            
            if more_img:
                try:
                    # Đọc thông tin deaths
                    gov_dead_img = self.preprocess_image3(more_img, (1130, 443, 183, 40))
                    if gov_dead_img is not None:
                        dead_text = self.read_ocr_from_image(gov_dead_img, "--psm 6 -c tessedit_char_whitelist=0123456789")
                        if dead_text:
                            gov_dead = dead_text
                    
                    # RSS Assistance
                    gov_rss_img = self.preprocess_image3(more_img, (1130, 668, 183, 40))
                    if gov_rss_img is not None:
                        rss_text = self.read_ocr_from_image(gov_rss_img, "--psm 6 -c tessedit_char_whitelist=0123456789")
                        if rss_text:
                            gov_rss_assistance = rss_text
                    
                    # Alliance helps
                    gov_helps_img = self.preprocess_image3(more_img, (1148, 732, 164, 44))
                    if gov_helps_img is not None:
                        helps_text = self.read_ocr_from_image(gov_helps_img, "--psm 6 -c tessedit_char_whitelist=0123456789")
                        if helps_text:
                            gov_alliance_helps = helps_text
                except Exception as e:
                    print(f"Error reading more info: {e}")
            
            # Đóng tab More Info
            self.device.shell('input tap 1396 58')
            
            # In thông tin debug
            self._print_governor_info_full(gov_id, gov_name, gov_power, gov_killpoints, gov_dead,
                                           kills_tiers, gov_rss_assistance, gov_alliance_helps, 
                                           alliance_tag, gov_kills_high, gov_deads_high, gov_sevs_high)
            
            # Ghi vào Excel
            self._write_full_data(sheet, i, j, gov_name, gov_id, gov_power, gov_killpoints, gov_dead,
                                 kills_tiers[0], kills_tiers[1], kills_tiers[2], kills_tiers[3], kills_tiers[4],
                                 gov_rss_assistance, gov_alliance_helps, alliance_tag, 
                                 gov_kills_high, gov_deads_high, gov_sevs_high)
            
            return True
        except Exception as e:
            print(f"Error in scan_governor_full: {e}")
            return False
    
    def _print_governor_info_full(self, gov_id, gov_name, gov_power, gov_killpoints, gov_dead, 
                                tier_kills, rss_assistance, alliance_helps, alliance_tag, kvk_kills, kvk_deads, kvk_sevs):
        """Print full governor information"""
        print(f'Governor ID: {gov_id}\nGovernor Name: {gov_name}')
        print(f'Governor Power: {self._format_int(gov_power)}')
        print(f'Governor Killpoints: {self._format_int(gov_killpoints)}')
        print(f'Governor Dead: {self._format_int(gov_dead)}')
        print(f'T1 Kills: {self._format_int(tier_kills[0])}')
        print(f'T2 Kills: {self._format_int(tier_kills[1])}')
        print(f'T3 Kills: {self._format_int(tier_kills[2])}')
        print(f'T4 Kills: {self._format_int(tier_kills[3])}')
        print(f'T5 Kills: {self._format_int(tier_kills[4])}')
        print(f'RSS Assistance: {self._format_int(rss_assistance)}')
        print(f'Alliance Helps: {self._format_int(alliance_helps)}')
        print(f'Alliance: {alliance_tag}')
        print(f'KvK Kills: {self._format_int(kvk_kills)}')
        print(f'KvK Deads: {self._format_int(kvk_deads)}')
        print(f'KvK Severely Wounded: {self._format_int(kvk_sevs)}')
        
    def _write_full_data(self, sheet, i, j, gov_name, gov_id, gov_power, gov_killpoints, gov_dead,
                        t1_kills, t2_kills, t3_kills, t4_kills, t5_kills,
                        rss_assistance, alliance_helps, alliance_tag, kvk_kills, kvk_deads, kvk_sevs):
        """Write full governor data to Excel"""
        row = i - j + 1
        sheet.write(row, 0, gov_name)
        sheet.write(row, 1, self._to_int_check(gov_id))
        sheet.write(row, 2, self._to_int_check(gov_power))
        sheet.write(row, 3, self._to_int_check(gov_killpoints))
        sheet.write(row, 4, self._to_int_check(gov_dead))
        sheet.write(row, 5, self._to_int_check(t1_kills))
        sheet.write(row, 6, self._to_int_check(t2_kills))
        sheet.write(row, 7, self._to_int_check(t3_kills))
        sheet.write(row, 8, self._to_int_check(t4_kills))
        sheet.write(row, 9, self._to_int_check(t5_kills))
        sheet.write(row, 10, self._to_int_check(rss_assistance))
        sheet.write(row, 11, self._to_int_check(alliance_helps))
        sheet.write(row, 12, alliance_tag)
        sheet.write(row, 13, self._to_int_check(kvk_kills))
        sheet.write(row, 14, self._to_int_check(kvk_deads))
        sheet.write(row, 15, self._to_int_check(kvk_sevs))
    
    def _print_governor_info_basic(self, gov_id, gov_name, gov_power, gov_killpoints):
        """Print basic governor information"""
        print(f'Governor ID: {gov_id}\nGovernor Name: {gov_name}\nGovernor Power: {self._format_int(gov_power)}\nGovernor Killpoints: {self._format_int(gov_killpoints)}')
    
    def _print_governor_info_pkd(self, gov_id, gov_name, gov_power, gov_killpoints, gov_dead):
        """Print Power + Kill Points + Dead governor information"""
        print(f'Governor ID: {gov_id}\nGovernor Name: {gov_name}\nGovernor Power: {self._format_int(gov_power)}\nGovernor Killpoints: {self._format_int(gov_killpoints)}\nGovernor Dead: {self._format_int(gov_dead)}')
    
    def _write_basic_data(self, sheet, i, j, gov_name, gov_id, gov_power, gov_killpoints):
        """Ghi dữ liệu cơ bản vào Excel"""
        sheet.write(i - j + 1, 0, gov_name)
        sheet.write(i - j + 1, 1, self._to_int_check(gov_id))
        sheet.write(i - j + 1, 2, self._to_int_check(gov_power))
        sheet.write(i - j + 1, 3, self._to_int_check(gov_killpoints))
    
    def _write_pkd_data(self, sheet, i, j, gov_name, gov_id, gov_power, gov_killpoints, gov_dead):
        """Ghi dữ liệu Power+Kill+Dead vào Excel"""
        sheet.write(i - j + 1, 0, gov_name)
        sheet.write(i - j + 1, 1, self._to_int_check(gov_id))
        sheet.write(i - j + 1, 2, self._to_int_check(gov_power))
        sheet.write(i - j + 1, 3, self._to_int_check(gov_killpoints))
        sheet.write(i - j + 1, 4, self._to_int_check(gov_dead))
    
    def _to_int_check(self, element):
        """Chuyển đổi giá trị sang integer nếu có thể"""
        try:
            return int(element)
        except ValueError:
            return element
    
    def _format_int(self, element):
        """Format integer với dấu phân cách hàng nghìn"""
        try:
            return f'{int(element):,}'
        except ValueError:
            return str(element)