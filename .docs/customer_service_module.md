# Customer Service Module Documentation

## Overview
Module Customer Service là hệ thống quản lý quy trình phục vụ khách hàng, từ bước tiếp nhận thông tin ban đầu đến hoàn thành dịch vụ. Hệ thống này cho phép theo dõi trạng thái của mỗi ticket dịch vụ, phân công nhiệm vụ cho các nhân viên ở từng bước, và tính toán chi phí dịch vụ.

## Key Features
1. **Quản lý Ticket**
   - Mã ticket tự động tạo theo định dạng YYMM-XXXX (Năm-Tháng-Số thứ tự)
   - Theo dõi trạng thái ticket xuyên suốt quy trình
   - Lưu trữ lịch sử thay đổi và ghi chú

2. **Quy trình dịch vụ đa bước**
   - Cấu hình linh hoạt các bước trong quy trình
   - Mỗi bước có nhân viên phụ trách riêng
   - Tự động tạo task khi bước trước hoàn thành

3. **Tính giá dịch vụ**
   - Mỗi bước có cấu hình giá riêng
   - Hỗ trợ nhiều mô hình tính giá (theo số lượng, theo yêu cầu)
   - Tạo báo giá tự động dạng PDF hoặc XLSX

4. **Phân công nhân viên**
   - Gán nhân viên cho từng bước trong quy trình
   - Theo dõi workload và hiệu suất của nhân viên
   - Thông báo khi có task mới được gán

## Database Models

### ServiceTicket
- `id`: Integer (Primary Key)
- `ticket_code`: String (YYMM-XXXX)
- `client_id`: Integer (Foreign Key)
- `sales_rep_id`: Integer (Foreign Key)
- `title`: String
- `description`: Text
- `status`: Enum (NEW, IN_PROGRESS, ON_HOLD, COMPLETED, CANCELLED)
- `priority`: Enum (LOW, MEDIUM, HIGH, URGENT)
- `created_at`: DateTime
- `updated_at`: DateTime
- `estimated_completion`: DateTime
- `actual_completion`: DateTime
- `total_price`: Decimal

### ServiceStep
- `id`: Integer (Primary Key)
- `name`: String
- `description`: Text
- `order`: Integer
- `is_active`: Boolean
- `estimated_duration_hours`: Float
- `pricing_model`: Enum (FIXED, PER_UNIT, HOURLY, CUSTOM)
- `base_price`: Decimal

### TicketStep
- `id`: Integer (Primary Key)
- `ticket_id`: Integer (Foreign Key)
- `step_id`: Integer (Foreign Key)
- `status`: Enum (PENDING, IN_PROGRESS, COMPLETED, SKIPPED)
- `assigned_staff_id`: Integer (Foreign Key)
- `quantity`: Integer
- `unit_price`: Decimal
- `total_price`: Decimal
- `start_date`: DateTime
- `completion_date`: DateTime
- `notes`: Text

### QuoteDocument
- `id`: Integer (Primary Key)
- `ticket_id`: Integer (Foreign Key)
- `document_type`: Enum (PDF, XLSX)
- `file_path`: String
- `created_at`: DateTime
- `created_by_id`: Integer (Foreign Key)
- `is_sent`: Boolean
- `sent_at`: DateTime

## API Endpoints

### Ticket Management
- `POST /api/customer-service/tickets`: Tạo ticket mới
- `GET /api/customer-service/tickets`: Lấy danh sách ticket
- `GET /api/customer-service/tickets/{ticket_id}`: Lấy thông tin chi tiết ticket
- `PUT /api/customer-service/tickets/{ticket_id}`: Cập nhật thông tin ticket
- `DELETE /api/customer-service/tickets/{ticket_id}`: Xóa ticket

### Step Management
- `POST /api/customer-service/steps`: Tạo bước mới
- `GET /api/customer-service/steps`: Lấy danh sách các bước
- `GET /api/customer-service/steps/{step_id}`: Lấy thông tin chi tiết bước
- `PUT /api/customer-service/steps/{step_id}`: Cập nhật thông tin bước
- `DELETE /api/customer-service/steps/{step_id}`: Xóa bước

### Ticket Step Operations
- `POST /api/customer-service/tickets/{ticket_id}/steps`: Thêm bước cho ticket
- `GET /api/customer-service/tickets/{ticket_id}/steps`: Lấy danh sách các bước của ticket
- `PUT /api/customer-service/tickets/{ticket_id}/steps/{step_id}`: Cập nhật trạng thái bước
- `POST /api/customer-service/tickets/{ticket_id}/steps/{step_id}/complete`: Hoàn thành bước

### Quote Generation
- `POST /api/customer-service/tickets/{ticket_id}/generate-quote`: Tạo báo giá
- `GET /api/customer-service/tickets/{ticket_id}/quotes`: Lấy danh sách báo giá

## Integration Points
- **User Module**: Xác thực và phân quyền người dùng
- **Client Module**: Thông tin khách hàng
- **Task Module**: Tạo và quản lý task cho nhân viên
- **Notification Module**: Thông báo khi có task mới hoặc trạng thái thay đổi

## Workflow Example
1. Sales tiếp nhận thông tin khách hàng và tạo ticket mới
2. Hệ thống tự động tạo mã ticket theo định dạng YYMM-XXXX
3. Sales có thể tạo báo giá dựa trên các bước dịch vụ và gửi cho khách hàng
4. Khi khách hàng xác nhận, sales cập nhật trạng thái ticket thành "IN_PROGRESS"
5. Hệ thống tự động tạo task cho nhân viên phụ trách bước đầu tiên
6. Khi nhân viên hoàn thành bước, họ cập nhật trạng thái và hệ thống tự động tạo task cho bước tiếp theo
7. Quy trình tiếp tục cho đến khi hoàn thành tất cả các bước
8. Sau khi hoàn thành, ticket được đánh dấu là "COMPLETED"
