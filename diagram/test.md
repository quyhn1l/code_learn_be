```mermaid
sequenceDiagram
    User->>NextJS: Click đăng nhập Google
    NextJS->>Google: Chuyển hướng đến trang Google
    Google->>NextJS: Callback với thông tin user
    Note over NextJS: NextAuth tự động xử lý:<br/>- Tạo session<br/>- Lưu user vào DB<br/>- Tạo JWT
    NextJS->>FastAPI: Gọi API với JWT từ NextAuth
    Note over FastAPI: Verify JWT và xử lý<br/>business logic
    FastAPI->>NextJS: Trả về data
    ```
    
