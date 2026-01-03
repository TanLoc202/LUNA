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
        print("Webhook data:", data)

        # Lấy mã chuyển khoản
        ma_chuyen_khoan = data.get("code") or data.get("content")
        so_tien_nhan = data.get("transferAmount")

        # 1. Kiểm tra trùng lặp giao dịch theo id
        existing_tx = supabase.table("tb_transactions").select("*").eq("id", data.get("id")).execute()
        if existing_tx.data:
            print("❌ Giao dịch đã tồn tại")
            return {"status": "ignored", "message": "Giao dịch đã tồn tại"}

        # 2. Lưu giao dịch mới (chỉ insert các trường cần thiết)
        supabase.table("tb_transactions").insert({
            "id": data.get("id"),
            "gateway": data.get("gateway"),
            "transactiondate": data.get("transactionDate"),
            "accountnumber": data.get("accountNumber"),
            "code": data.get("code"),
            "content": data.get("content"),
            "transfertype": data.get("transferType"),
            "transferamount": data.get("transferAmount"),
            "accumulated": data.get("accumulated"),
            "referencecode": data.get("referenceCode"),
            "description": data.get("description")
        }).execute()

        # 3. Kiểm tra đơn hàng
        res = supabase.table("don_hang").select("*").eq("ma_chuyen_khoan", ma_chuyen_khoan).execute()
        if not res.data:
            print("❌ Không tìm thấy đơn hàng")
            return {"status": "error", "message": "Không tìm thấy đơn hàng"}

        order = res.data[0]

        # 4. Kiểm tra số tiền (ép kiểu về float)
        if float(so_tien_nhan) == float(order['tong_tien']):
            supabase.table("don_hang").update({"trang_thai": "Đã thanh toán"}).eq("id", order['id']).execute()
            print(f"✅ Đơn hàng #{order['id']} đã thanh toán")
            return {"status": "success", "message": f"Đơn hàng #{order['id']} đã thanh toán"}
        else:
            print("❌ Số tiền không khớp")
            return {"status": "error", "message": "Số tiền không khớp"}

    except Exception as e:
        print(f"🔥 Lỗi xử lý: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
