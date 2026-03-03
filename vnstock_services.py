# from vnstock3 import Vnstock

# def get_stock_overview(symbol):
#     # Khởi tạo vnstock
#     stock = Vnstock().stock(symbol=symbol, source='VCI') # Có thể chọn source khác như 'TCBS'
    
#     try:
#         print(f"--- TỔNG QUAN MÃ {symbol.upper()} ---")
        
#         # 1. Lấy thông tin hồ sơ doanh nghiệp
#         profile = stock.profile()
#         print(f"Tên công ty: {profile.get('company_name', 'N/A')}")
#         print(f"Sàn: {profile.get('exchange', 'N/A')}")
#         print(f"Ngành: {profile.get('industry', 'N/A')}")
        
#         # 2. Lấy các chỉ số tài chính cơ bản (Overview)
#         # Trong vnstock3, thông tin này thường nằm trong ratio hoặc tài chính nhanh
#         ratios = stock.finance.ratio(period='yearly', lang='vi')
        
#         if not ratios.empty:
#             # Lấy dòng mới nhất (năm gần nhất)
#             latest = ratios.iloc[0]
#             print(f"\n📊 Chỉ số tài chính chính:")
#             print(f"- P/E: {latest.get('p_e', 'N/A')}")
#             print(f"- P/B: {latest.get('p_b', 'N/A')}")
#             print(f"- ROE: {latest.get('roe', 'N/A')}%")
#             print(f"- EPS: {latest.get('eps', 'N/A')} VNĐ")
        
#         print("\n📝 Mô tả kinh doanh:")
#         print(profile.get('description', 'Không có mô tả.'))

#     except Exception as e:
#         print(f"❌ Lỗi khi lấy dữ liệu cho mã {symbol}: {e}")

# if __name__ == "__main__":
#     ticker = input("Nhập mã cổ phiếu (vd: VCB, FPT, HPG): ").upper()
#     get_stock_overview(ticker)