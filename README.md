# IoT Lab 2 — Thu thập, lưu trữ và tiền xử lý dữ liệu IoT

## 1. Giới thiệu

Bài thực hành số 2 — Học phần IoT và Ứng dụng (INT14149).

Xây dựng hệ thống thu thập dữ liệu cảm biến từ ESP32 mô phỏng trên Wokwi qua MQTT, kiểm tra dữ liệu bằng Python, lưu vào InfluxDB và thực hiện tiền xử lý dữ liệu time-series.

Hệ thống sử dụng dữ liệu mô phỏng từ Wokwi và dữ liệu bổ sung được sinh bằng Python để kiểm thử.

## 2. Kiến trúc hệ thống

```text
Wokwi ESP32
  ├── DHT22 (temperature, humidity)
  └── HC-SR04 (distance)
           |
           | MQTT / JSON
           v
HiveMQ Public Broker
           |
           | Subscribe
           v
Python MQTT Client
  ├── JSON Validation
  └── InfluxDB Write
           |
           v
InfluxDB 2.9.1
  ├── sensor_data
  └── sensor_processed
           |
           +---- Python Preprocessing
           |
           +---- InfluxDB Dashboard
```

## 3. Công nghệ

| Thành phần | Công nghệ |
|---|---|
| Thiết bị mô phỏng | ESP32 — Wokwi |
| Cảm biến | DHT22, HC-SR04 |
| Giao thức | MQTT |
| MQTT Broker | HiveMQ Public Broker |
| Ngôn ngữ | Python 3.11 |
| Database | InfluxDB 2.9.1 |
| Xử lý dữ liệu | pandas, numpy |
| Dashboard | InfluxDB Dashboard |

## 4. Cấu trúc project

```text
iot-lab2/
├── mqtt_client.py
├── preprocessing.py
├── seed_data.py
├── requirements.txt
├── README.md
├── .gitignore
└── Screenshot 2026-10-11 101145.png
```

Firmware ESP32 được triển khai trên Wokwi, kế thừa project của bài thực hành số 1.

## 5. Cấu hình hệ thống

MQTT Broker:

- Host: `broker.hivemq.com`
- Port: `1883`
- Topic: `ptit/iot/cuongdso/lab2/telemetry`

InfluxDB:

- URL: `http://localhost:8086`
- Organization: `admin`
- Bucket: `iot-th-2`
- Measurement dữ liệu gốc: `sensor_data`
- Measurement dữ liệu xử lý: `sensor_processed`

Cần cấu hình InfluxDB API Token hợp lệ trong môi trường chạy trước khi sử dụng. Không đưa token thật lên GitHub.

## 6. Hướng dẫn chạy

### 6.1. Chuẩn bị Python

Tạo môi trường ảo:

```powershell
python -m venv .venv
```

Cài thư viện:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 6.2. Khởi động InfluxDB

Khởi động InfluxDB 2.x bằng `influxd`.

Truy cập `http://localhost:8086`, tạo Organization và bucket theo cấu hình ở mục 5.

### 6.3. Thu thập dữ liệu MQTT

Khởi động project ESP32 trên Wokwi.

Chạy:

```powershell
.\.venv\Scripts\python.exe mqtt_client.py
```

Python sẽ subscribe MQTT, validate JSON và ghi dữ liệu hợp lệ vào InfluxDB.

Dừng bằng `Ctrl + C`.

### 6.4. Sinh dữ liệu kiểm thử (tùy chọn)

```powershell
.\.venv\Scripts\python.exe seed_data.py
```

Script tạo 120 bản ghi mô phỏng có giá trị thiếu và outlier nhằm kiểm thử thuật toán tiền xử lý.

### 6.5. Tiền xử lý

```powershell
.\.venv\Scripts\python.exe preprocessing.py
```

Các bước xử lý:

1. Đọc dữ liệu từ InfluxDB.
2. Xử lý missing values bằng linear interpolation.
3. Phát hiện outlier bằng IQR, thay thế bằng median.
4. Resampling dữ liệu theo cửa sổ 10 giây.
5. Tính rolling mean và delta.
6. Chuẩn hóa Min-Max.
7. Ghi dữ liệu đã xử lý vào measurement `sensor_processed`.

### 6.6. Dashboard

Truy cập `http://localhost:8086` và tạo dashboard `IoT Lab 2 - Monitoring`.

Dashboard hiển thị:

- Temperature - Raw Data
- Temperature - Processed Data

Có thể bật Auto Refresh để cập nhật dữ liệu mới.

## 7. Kết quả thực nghiệm

| Chỉ tiêu | Kết quả |
|---|---:|
| Số bản ghi đầu vào | 200 |
| Missing values được xử lý | 9 |
| Outlier nhiệt độ phát hiện | 63 |
| Outlier độ ẩm phát hiện | 6 |
| Outlier khoảng cách phát hiện | 0 |
| Chu kỳ resampling | 10 giây |
| Số bản ghi sau xử lý | 190 |

Các kết quả trên được ghi nhận trong phiên thực hành ngày 11/10/2026.

### Đánh giá hiệu năng

Thực hiện đo 22 lần ghi dữ liệu từ Python tới InfluxDB bằng `time.perf_counter()`:

- Độ trễ ghi nhỏ nhất: 2.44 ms
- Độ trễ ghi trung bình: khoảng 7.13 ms
- Độ trễ ghi lớn nhất: 57.59 ms

Các phép đo chỉ phản ánh thời gian thực hiện thao tác ghi InfluxDB, chưa bao gồm độ trễ truyền qua MQTT từ ESP32 tới Python.

## 8. Hạn chế

- ESP32 và cảm biến đang chạy mô phỏng trên Wokwi.
- Dữ liệu seed được tạo bằng Python, không phải dữ liệu đo vật lý.
- MQTT Public Broker không cung cấp kênh truyền riêng tư.
- Chưa đo độ trễ end-to-end toàn hệ thống.
- Dữ liệu đã xử lý được cập nhật bằng cách chạy script theo lô, chưa được xử lý liên tục.
- Cần cấu hình retention policy phù hợp khi triển khai dài hạn.

## 9. Kết luận

Hệ thống đã triển khai thành công luồng thu thập MQTT, kiểm tra dữ liệu đầu vào, lưu dữ liệu time-series, tiền xử lý và trực quan hóa trên dashboard InfluxDB.

Mô hình đáp ứng các chức năng thực hành chính với kiến trúc đơn giản, phù hợp cho mục đích học tập và thực nghiệm.
