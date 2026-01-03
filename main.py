import os
from fastapi import FastAPI, Request, HTTPException
from supabase import create_client, Client

app = FastAPI()
# --- CẤU HÌNH SUPABASE ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- CÁC HÀM CHÍNH ---
@app.get("/")
def home():
    return {"status": "online", "message": "Hệ thống Luna Store đang hoạt động!"}

# --- WEBHOOK NHẬN TIỀN TỪ SEPAY ---
@app.post("/webhook/sepay")
async def receive_payment(request: Request):
    try:
        data = await request.json()

        ma_chuyen_khoan = data.get("code")
        so_tien_nhan = data.get("transferAmount")  # SePay gửi ở trường transferAmount

        # Nếu code null, fallback sang content
        if not ma_chuyen_khoan:
            ma_chuyen_khoan = data.get("content")

        # 1. Kiểm tra trùng lặp giao dịch
        existing_tx = supabase.table("tb_transactions").select("*").eq("id", data.get("id")).execute()
        if existing_tx.data:
            return {"status": "ignored", "message": "Giao dịch đã tồn tại"}

        # 2. Lưu giao dịch mới
        supabase.table("tb_transactions").insert(data).execute()

        # 3. Kiểm tra đơn hàng
        res = supabase.table("don_hang").select("*").eq("ma_chuyen_khoan", ma_chuyen_khoan).execute()
        if not res.data:
            return {"status": "error", "message": "Không tìm thấy đơn hàng"}

        order = res.data[0]

        # 4. Kiểm tra số tiền
        if so_tien_nhan == order['tong_tien']:
            supabase.table("don_hang").update({"trang_thai": "Đã thanh toán"}).eq("id", order['id']).execute()
            return {"status": "success", "message": f"Đơn hàng #{order['id']} đã thanh toán"}
        else:
            return {"status": "error", "message": "Số tiền không khớp"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
