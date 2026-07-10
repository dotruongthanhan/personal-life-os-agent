import os.path
from datetime import datetime, timezone, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv
import zoneinfo

SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',  # Quyền Tạo/Sửa/Xóa sự kiện
    'https://www.googleapis.com/auth/calendar.readonly' # Quyền Đọc danh sách lịch và cài đặt
]
load_dotenv()

CALENDAR_ID_PERSONAL = os.getenv("CALENDAR_ID_PERSONAL", "primary")

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

def list_user_calendars():
    """Lấy danh sách tên và ID các lịch của người dùng."""
    service = get_calendar_service()
    calendar_list = service.calendarList().list().execute()
    return [{"id": cal["id"], "summary": cal["summary"]} for cal in calendar_list['items']]

def get_raw_events_today():
    """Hàm lõi để lấy danh sách sự kiện thô từ Google"""
    service = get_calendar_service()
    calendar_ids = get_calendar_ids_from_env()
    
    # Lấy múi giờ linh hoạt
    try:
        primary_cal = service.calendars().get(calendarId=calendar_ids[0]).execute()
        tz_name = primary_cal.get('timeZone', 'Asia/Ho_Chi_Minh')
    except:
        tz_name = 'Asia/Ho_Chi_Minh'
    
    user_tz = zoneinfo.ZoneInfo(tz_name)
    now = datetime.now(user_tz)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)

    all_items = []
    for cal_id in calendar_ids:
        try:
            result = service.events().list(
                calendarId=cal_id,
                timeMin=now.isoformat(),
                timeMax=end_of_day.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            all_items.extend(result.get('items', []))
        except Exception as e:
            print(f"⚠️ Lỗi đọc {cal_id}: {e}")
            
    return all_items, user_tz, now

def get_clean_events_today():
    """Hàm wrapper để gọi get_raw_events_today và trả về kết quả đã được xử lý"""
    events, user_tz, _ = get_raw_events_today()
    if not events:
        return []
    
    # Chuyển đổi thời gian về múi giờ người dùng và định dạng lại
    clean_events = []
    
    for event in events:
        # 1. Xử lý thời gian (lấy dateTime hoặc date cho sự kiện cả ngày)
        start_raw = event['start'].get('dateTime', event['start'].get('date'))
        end_raw = event['end'].get('dateTime', event['end'].get('date'))
        
        # Chuyển đổi sang múi giờ người dùng để AI dễ đọc
        start_dt = datetime.fromisoformat(start_raw.replace('Z', '+00:00')).astimezone(user_tz)
        end_dt = datetime.fromisoformat(end_raw.replace('Z', '+00:00')).astimezone(user_tz)
        
        # 2. Chỉ trích xuất các trường thiết yếu
        clean_event = {
            "event_id": event.get('id'),
            "summary": event.get('summary', 'Không có tiêu đề'),
            "description": event.get('description', ''),
            "start": start_dt.strftime('%Y-%m-%d %H:%M'),
            "end": end_dt.strftime('%Y-%m-%d %H:%M'),
            "location": event.get('location', '')
        }
        clean_events.append(clean_event)
    
    return clean_events

def get_upcoming_events():
    """Lấy danh sách sự kiện sắp tới"""

    all_events, _, __ = get_raw_events_today()
    if not all_events:
        return '📭 Không tìm thấy sự kiện nào trong ngày hôm nay.'

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
        location = event.get('location')
        description = event.get('description')

        event_block = f"{time_str} | 📌 **{summary}**\n"
        if location:
            event_block += f"   📍 *Địa điểm:* {location}\n"
        if description:
            event_block += f"   📝 *Mô tả:* {description}\n"
        event_block += f"━━━━━━━━━━━━━━━━━━━━"
        result_lines.append(event_block)

    return result + "\n".join(result_lines)

def fetch_calendar_reminders(default_minutes: int = 30):
    """
    Lấy danh sách các mốc thông báo từ Google Calendar.
    Mặc định nhắc trước 30 phút nếu event không có reminder.
    """
    events, user_tz, now = get_raw_events_today()
    new_notifications = {}

    for event in events:
        start_raw = event['start'].get('dateTime', event['start'].get('date'))
        start_dt = datetime.fromisoformat(start_raw.replace('Z', '+00:00')).astimezone(user_tz)

        # Lấy cấu hình reminders từ Google
        reminders = event.get('reminders', {})
        if reminders.get('useDefault'):
            # Nếu dùng mặc định của Google Calendar (thường là 10-30p) 
            # hoặc bạn có thể ép về default_minutes của bạn ở đây
            minutes_list = [default_minutes]
        else:
            overrides = reminders.get('overrides', [])
            # Nếu có cài đặt riêng thì lấy, không thì dùng default_minutes
            minutes_list = [ov.get('minutes') for ov in overrides] if overrides else [default_minutes]

        for m in minutes_list:
            notify_dt = start_dt - timedelta(minutes=int(m))
            # Chỉ lấy các mốc ở tương lai
            if notify_dt > now:
                notify_iso = notify_dt.isoformat()
                event_info = {
                    'summary': event.get('summary', '(Không tiêu đề)'),
                    'start': start_dt.strftime('%H:%M'),
                    'location': event.get('location'),
                    'description': event.get('description'),
                    'reminder_minutes': m
                }
                new_notifications.setdefault(notify_iso, []).append(event_info)

    return new_notifications

def create_event(summary: str, start: str, calendar_id: str = CALENDAR_ID_PERSONAL,
                 duration_minutes: int = 60, description: str = "", location: str = ""):
    """
    Tạo sự kiện trên một lịch cụ thể với múi giờ tự động khớp với lịch đó.
    - start: Chuỗi thời gian (VD: "2026-03-20 15:00")
    - calendar_id: ID của lịch (mặc định là 'primary')
    """
    service = get_calendar_service()

    try:
        # 1. Lấy múi giờ của Calendar mục tiêu
        calendar_info = service.calendars().get(calendarId=calendar_id).execute()
        tz_name = calendar_info.get('timeZone', 'UTC')
        user_tz = zoneinfo.ZoneInfo(tz_name)

        # 2. Xử lý thời gian dựa trên múi giờ của lịch
        # Giả sử AI hoặc User nhập "2026-03-20 15:00", ta gán múi giờ của lịch vào
        naive_start = datetime.strptime(start, "%Y-%m-%d %H:%M")
        localized_start = naive_start.replace(tzinfo=user_tz)
        localized_end = localized_start + timedelta(minutes=duration_minutes)

        event_body = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {'dateTime': localized_start.isoformat(), 'timeZone': tz_name},
            'end': {'dateTime': localized_end.isoformat(), 'timeZone': tz_name},
        }

        event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        return {
            "status": "success", 
            "event_title": event.get('summary'),
            "calendar": calendar_info.get('summary'),
            "timezone": tz_name
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
    
def update_event(event_id: str = None, calendar_id: str = CALENDAR_ID_PERSONAL, summary: str = None,
                 start: str = None, end: str = None, description: str = None,
                 location: str = None, **kwargs):
    """
    Cập nhật một sự kiện đã có dựa trên id.
    """
    # Xử lý trường hợp LLM truyền nhầm argument 'id' thay vì 'event_id'
    event_id = event_id or kwargs.get('id')

    service = get_calendar_service()
    
    try:
        # Lấy múi giờ của Calendar mục tiêu
        calendar_info = service.calendars().get(calendarId=calendar_id).execute()
        tz_name = calendar_info.get('timeZone', 'UTC')
        user_tz = zoneinfo.ZoneInfo(tz_name)

        # Lấy dữ liệu hiện tại của sự kiện
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        
        if summary:
            # The summary is updated directly without emoji logic.
            event['summary'] = summary

        if start:
            # Xử lý giờ + múi giờ --> Giờ ISO với múi giờ của lịch
            naive_start = datetime.strptime(start, "%Y-%m-%d %H:%M")
            localized_start = naive_start.replace(tzinfo=user_tz)
            event['start'] = {'dateTime': localized_start.isoformat()}

        if end:
            # Xử lý giờ + múi giờ --> Giờ ISO với múi giờ của lịch
            naive_end = datetime.strptime(end, "%Y-%m-%d %H:%M")
            localized_end = naive_end.replace(tzinfo=user_tz)
            event['end'] = {'dateTime': localized_end.isoformat()}
            
        if description: event['description'] = description
        if location: event['location'] = location

        updated_event = service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
        return {"status": "success", "updated_title": updated_event.get('summary')}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    print("🔄 Đang lấy lịch trình sắp tới...")
    print(get_upcoming_events())
    print(get_raw_events_today())