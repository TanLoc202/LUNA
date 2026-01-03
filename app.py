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
        res = supabase.table("tb_transactions").insert(data).execute()

        # SePay gửi nội dung chuyển khoản ở trường 'content'
        ma_chuyen_khoan = data.get("code")
        so_tien_nhan = data.get("amount")

        # 1. Kiểm tra xem mã chuyển khoản này có khớp với đơn hàng nào trong DB không
        res = supabase.table("don_hang").select("*").eq("ma_chuyen_khoan", ma_chuyen_khoan).execute()
        
        if not res.data:
            print(f"❌ Không tìm thấy đơn hàng với mã: {ma_chuyen_khoan}")
            print(f"Received data: {data}")
            return {"status": "error", "message": "Mã đơn hàng hông khớp"}

        # 2. Nếu tìm thấy, cập nhật trạng thái thành 'Đã thanh toán'
        if so_tien_nhan >= res.data[0]['tong_tien']:   
            order_id = res.data [0]['id']
            supabase.table("don_hang").update({"trang_thai": "Đã thanh toán"}).eq("id", order_id).execute()
            print(f"✅ Đơn hàng #{order_id} đã thanh toán thành công!")
            return {"status": "success", "message": f"Đã chốt đơn #{order_id}"}

    except Exception as e:
        print(f"🔥 Lỗi xử lý: {str(e)}")
        raise HTTPException(status_code=500, detail="Lỗi server rồi bà chủ ơi")
