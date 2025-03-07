# Rok Scan Data

## 📌 Giới Thiệu

**Rok Scan Data** là công cụ tự động hóa thu thập dữ liệu từ game **Rise of Kingdoms**. Ứng dụng sử dụng công nghệ **OCR (Nhận dạng ký tự quang học)** để quét và trích xuất thông tin người chơi, liên minh và số liệu thống kê KvK.

## ✨ Tính Năng Chính

- 🔍 **Quét thông tin governor (người chơi):** ID, tên, sức mạnh, kill points
- 📊 **Trích xuất dữ liệu KvK:** kills, deaths, severely wounded
- 📱 **Hỗ trợ đa thiết bị thông qua LDPlayer**
- ⚡ **Cơ chế quét song song** giúp tối ưu hóa thời gian xử lý
- 📂 **Xuất dữ liệu sang định dạng Excel**

## 🖥️ Yêu Cầu Hệ Thống

- **Python** 3.7 trở lên
- **Tesseract OCR**
- **LDPlayer** (để chạy giả lập Android)
- Các thư viện Python cần thiết: `opencv`, `numpy`, `pytesseract`, `pandas`, `xlwt`, ... (được liệt kê trong `requirements.txt`)

## 🔧 Cài Đặt

### 1️⃣ Clone Repository
```bash
git clone https://github.com/username/rokscandata.git
cd rokscandata 
```

### 2️⃣ Cài Đặt Các Thư Viện Cần Thiết
```bash
pip install -r requirements.txt
```

### 3️⃣ Chạy Script Setup để Cấu Hình Môi Trường
```bash
python setup.py
```

### 4️⃣ Cấu Hình Đường Dẫn **Tesseract** và **LDPlayer**
Chỉnh sửa tệp `config/config.json` theo thiết lập của bạn.

## 🚀 Sử Dụng

### 1️⃣ Khởi Động Ứng Dụng
```bash
python main.py
```

### 2️⃣ Cấu Hình Thiết Bị
Tùy chỉnh thiết bị trong giao diện người dùng.

### 3️⃣ Chọn Chế Độ Quét
- **Governor** (Người chơi)
- **Alliance** (Liên minh)
- **KvK Stats** (Thống kê KvK)

### 4️⃣ Bắt Đầu Quét
Nhấn **Start** để khởi động quá trình quét dữ liệu.

## 📂 Cấu Trúc Dự Án
```
📁 scanner/       # Mô-đun quét và xử lý hình ảnh
📁 config/        # Tệp cấu hình
📁 data/          # Lưu trữ dữ liệu đầu ra
📁 screenshots/   # Lưu trữ ảnh chụp màn hình
📁 Ldplayer/      # Module giao tiếp với giả lập LDPlayer
```

## 🤝 Đóng Góp
Mọi đóng góp đều được hoan nghênh! Vui lòng mở **issue** để báo cáo lỗi hoặc đề xuất tính năng mới.

## 💖 Ủng Hộ Dự Án
Nếu bạn thấy **Rok Scan Data** hữu ích và muốn hỗ trợ phát triển, có thể ủng hộ qua:


- **Ngân hàng**: `MB Bank - 7700113112001 (Lâm Vũ Minh Nhật)`
- **PayPal**: `https://paypal.me/minhat1`

Mọi khoản ủng hộ sẽ giúp duy trì và phát triển dự án! 💙

## 👤 Tác Giả
- **Minnyat**

## 📜 Giấy Phép
Dự án này được phân phối dưới giấy phép **MIT License**.

## 📬 Liên Hệ
- ✉ **Email**: contact@minnyat.dev
- 💬 **Discord**: _minhat
- 🏠 **GitHub**: [github.com/lvminhnhat](https://github.com/lvminhnhat)

> **Lưu ý:** RokTracker Remake không phải là sản phẩm chính thức của **Lilith Games** và không liên kết với nhà phát triển **Rise of Kingdoms**. Công cụ này được tạo ra chỉ nhằm mục đích hỗ trợ người chơi trong việc thu thập dữ liệu. 🎮

