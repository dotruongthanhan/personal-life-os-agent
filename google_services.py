import os.path
from datetime import datetime, timezone, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_calendar_service():
    """Khởi tạo và xác thực dịch vụ Google Calendar API"""
    creds = None
    # 1. Kiểm tra xem đã có token (phiên đăng nhập) chưa
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # 2. Nếu chưa có hoặc token hết hạn thì đăng nhập lại
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Mở trình duyệt để user đăng nhập
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Lưu lại token cho lần sau đỡ phải đăng nhập
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # 3. Kết nối API
    service = build('calendar', 'v3', credentials=creds)
    return service

def get_calendars():
    """Lấy danh sách các calendar của user"""
    service = get_calendar_service()
    calendar_list = service.calendarList().list().execute()
    calendars = calendar_list.get('items', [])
    
    print("📋 Danh sách Calendar:")
    for cal in calendars:
        print(f"- {cal['summary']} (ID: {cal['id']})")

def get_upcoming_events():
    """Lấy danh sách sự kiện sắp tới"""
    service = get_calendar_service()

    # Lấy thời gian hiện tại theo định dạng chuẩn ISO (UTC)
    now = datetime.now(timezone.utc).isoformat()
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    
    events_result = service.events().list(
        calendarId='primary', 
        timeMin=now,
        timeMax=tomorrow,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])

    if not events:
        return ('📭 Không tìm thấy sự kiện nào sắp tới.')

    # Tạo string
    result = ("\n📅 --- LỊCH TRÌNH 24 GIỜ TỚI ---\n")
    result_lines = []
    for event in events:
        # 1. Lấy dữ liệu thô và xử lý ký tự 'Z' (nếu có) để Python đọc được
        start_raw = event['start'].get('dateTime', event['start'].get('date')).replace('Z', '+00:00')
        end_raw = event['end'].get('dateTime', event['end'].get('date')).replace('Z', '+00:00')
        
        # 2. Chuyển đổi chuỗi thành object datetime
        start_dt = datetime.fromisoformat(start_raw)
        end_dt = datetime.fromisoformat(end_raw)
        
        # 3. Format chỉ lấy Giờ:Phút (HH:MM)
        start_str = start_dt.strftime('%H:%M')
        end_str = end_dt.strftime('%H:%M')
        
        # 4. Kiểm tra điều kiện qua ngày
        if end_dt.date() > start_dt.date():
            end_str += " +1 day"
            
        # 5. Xử lý trường hợp event không có tiêu đề để tránh lỗi KeyError
        summary = event.get('summary', '(Không có tiêu đề)')
        
        # 6. Format text theo yêu cầu và thêm vào list
        result_lines.append(f"⏰ {start_str} to {end_str} | 📌 {summary}")

    # 7. Trả về chuỗi kết quả
    return result + "\n".join(result_lines)

# print(get_upcoming_events())