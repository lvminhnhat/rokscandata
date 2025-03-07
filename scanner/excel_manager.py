# scanner/excel_manager.py
import xlwt
from datetime import date

class ExcelManager:
    def setup_excel(self, scan_option):
        """
        Chuẩn bị file Excel cho kết quả quét
        
        Args:
            scan_option (int): Loại quét (1=đầy đủ, 2=basic, 3=power+kills+dead)
            
        Returns:
            tuple: (workbook, sheet)
        """
        wb = xlwt.Workbook()
        sheet1 = wb.add_sheet(str(date.today()))
        
        # Tạo style cho header
        style = xlwt.XFStyle()
        font = xlwt.Font()
        font.bold = True
        style.font = font
        
        # Chọn headers phù hợp với scan_option
        headers = self._get_headers_for_option(scan_option)
            
        # Thêm headers vào sheet
        for col, header in enumerate(headers):
            sheet1.write(0, col, header, style)
            
        return wb, sheet1
    
    def _get_headers_for_option(self, scan_option):
        """Lấy danh sách headers phù hợp với loại quét"""
        if scan_option == 1:
            # Full scan
            return [
                'Governor Name', 'Governor ID', 'Power', 'Kill Points', 'Deads', 
                'Tier 1 Kills', 'Tier 2 Kills', 'Tier 3 Kills', 'Tier 4 Kills', 
                'Tier 5 Kills', 'Rss Assistance', 'Alliance Helps', 'Alliance',
                'KvK Kills High', 'KvK Deads High', 'KvK Severely Wounds High'
            ]
        elif scan_option == 3:
            # Power, kills, deads only
            return ['Governor Name', 'Governor ID', 'Power', 'Kill Points', 'Deads']
        else:  # Option 2 or default
            # Basic scan
            return ['Governor Name', 'Governor ID', 'Power', 'Kill Points']
    
    def save_workbook(self, workbook, filepath):
        """
        Lưu workbook vào file
        
        Args:
            workbook: Workbook Excel cần lưu
            filepath: Đường dẫn đến file
            
        Returns:
            bool: True nếu thành công, False nếu lỗi
        """
        try:
            workbook.save(filepath)
            return True
        except Exception as e:
            print(f"Error saving workbook: {e}")
            return False