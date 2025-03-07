import os
import time
import subprocess

class Device:
    def __init__(self, device_id, ldplayer_path):
        """
        Khởi tạo thiết bị
        
        Args:
            device_id: ID của thiết bị
            ldplayer_path: Đường dẫn đến LDPlayer
        """
        self.id = str(device_id)
        self.ldplayer_path = ldplayer_path
        self.ldconsole = os.path.join(ldplayer_path, 'ldconsole.exe')
        
        # Kiểm tra ldconsole.exe
        if not os.path.isfile(self.ldconsole):
            raise FileNotFoundError(f"ldconsole.exe not found at {self.ldconsole}")
    
    def is_running(self):
        """Kiểm tra xem thiết bị có đang chạy không"""
        try:
            result = subprocess.run(
                [self.ldconsole, 'isrunning', '--index', self.id],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return "running" in result.stdout.lower()
        except Exception as e:
            print(f"Error checking device status: {e}")
            return False
    
    def shell(self, command):
        """
        Thực thi lệnh trên thiết bị
        
        Args:
            command: Lệnh cần thực thi
            
        Returns:
            str: Kết quả lệnh
        """
        try:
            # Sử dụng ldconsole để thực hiện lệnh
            full_command = [self.ldconsole, 'adb', '--index', self.id, '--command', command]
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.stdout
        except Exception as e:
            print(f"Error executing command: {e}")
            return ""
    
    def capture_screenshot(self, output_file):
        """
        Chụp màn hình thiết bị
        
        Args:
            output_file: Đường dẫn file đầu ra
            
        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        try:
            # Đảm bảo thư mục tồn tại
            output_dir = os.path.dirname(output_file)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Sử dụng lệnh screencap của ADB
            self.shell(f'screencap -p /sdcard/screenshot.png')
            time.sleep(0.5)  # Chờ thiết bị hoàn thành chụp ảnh
            
            # Kéo file về máy tính
            try:
                # Phương pháp 1: Sử dụng ldconsole adb pull
                pull_command = [
                    self.ldconsole, 'adb', 
                    '--index', self.id, 
                    '--command', f'pull /sdcard/screenshot.png "{output_file}"'
                ]
                
                # Sử dụng _get_creation_flags để xử lý trường hợp CREATE_NO_WINDOW không tồn tại
                creation_flags = self._get_creation_flags() if hasattr(self, '_get_creation_flags') else 0
                
                result = subprocess.run(
                    pull_command,
                    capture_output=True,
                    text=True,
                    creationflags=creation_flags
                )
                
                # Kiểm tra kết quả
                if not os.path.exists(output_file) or os.path.getsize(output_file) < 100:
                    print(f"Pull method 1 failed, trying method 2...")
                    # Phương pháp 2: Lưu trực tiếp dữ liệu từ ADB
                    self.shell(f'cat /sdcard/screenshot.png > "{output_file}"')
                    time.sleep(0.5)
            except Exception as e:
                print(f"Error pulling screenshot: {e}")
                return False
            
            # Kiểm tra xem file có tồn tại không
            if os.path.exists(output_file) and os.path.getsize(output_file) > 100:
                return True
            else:
                print(f"Screenshot exists but is too small: {output_file}")
                return False
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return False