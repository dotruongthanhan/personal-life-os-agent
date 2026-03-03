import os.path
from datetime import datetime, timezone, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
load_dotenv()

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

def get_calendar_ids_from_env():
    """Quét và lấy tất cả giá trị của các biến bắt đầu bằng CALENDAR_ID_"""
    calendar_ids = []
    
    # os.environ chứa tất cả biến môi trường hiện có
    for key, value in os.environ.items():
        if key.startswith("CALENDAR_ID_"):
            calendar_ids.append(value)
            
    return calendar_ids

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
    
    calendar_ids = get_calendar_ids_from_env()
    all_events = []
    # 1. Lặp qua từng calendar để lấy sự kiện
    for cal_id in calendar_ids:
        try:
            events_result = service.events().list(
                calendarId=cal_id, 
                timeMin=now,
                timeMax=tomorrow,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            all_events.extend(events) # Thêm vào danh sách tổng
        except Exception as e:
            print(f"⚠️ Lỗi khi đọc calendar {cal_id}: {e}")

    if not all_events:
        return '📭 Không tìm thấy sự kiện nào trong 24 giờ tới.'

    # 2. Sắp xếp tất cả sự kiện theo thời gian bắt đầu (startTime)
    # Chúng ta dùng get('dateTime') cho sự kiện có giờ, và get('date') cho sự kiện cả ngày
    all_events.sort(key=lambda x: x['start'].get('dateTime', x['start'].get('date')))

    # 3. Tạo chuỗi kết quả trả về
    result = ""
    result_lines = []
    
    for event in all_events:
        # Lấy thời gian
        start_raw = event['start'].get('dateTime', event['start'].get('date')).replace('Z', '+00:00')
        end_raw = event['end'].get('dateTime', event['end'].get('date')).replace('Z', '+00:00')
        start_dt = datetime.fromisoformat(start_raw)
        end_dt = datetime.fromisoformat(end_raw)
        
        time_str = f"⏰ **{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}**"
        
        # Lấy thông tin bổ sung
        summary = event.get('summary', '(Không có tiêu đề)')
        location = event.get('location', 'Không có địa điểm')
        description = event.get('description', 'Không có mô tả')

        # Format block cho 1 sự kiện
        event_block = (
            f"{time_str} | 📌 **{summary}**\n"
            f"   📍 *Địa điểm:* {location}\n"
            f"   📝 *Mô tả:* {description}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        result_lines.append(event_block)

    return result + "\n".join(result_lines)

# print(get_upcoming_events())