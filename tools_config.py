from weather_service import get_weather_forecast_data
from google_services import get_clean_events, create_event, list_user_calendars, update_event

tools = [
    {
        "type": "function",
        "name": "get_weather_forecast_data",
        "description": "Lấy dữ liệu dự báo thời tiết cho một ngày cụ thể ở một thành phố.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "Thành phố hoặc tên quốc gia"},
                "target_date_str": {"type": "string", "description": "Ngày muốn xem thời tiết theo định dạng 'YYYY-MM-DD'. Bỏ trống nếu là hôm nay."}
            },
            "required": ["location"]
        }
    },
    {
        "type": "function",
        "name": "get_clean_events",
        "description": "Lấy danh sách sự kiện từ lịch. Nếu không có ngày cụ thể, sẽ lấy sự kiện trong 30 ngày tới. Dùng hàm này để lấy event_id cho việc cập nhật hoặc xóa sự kiện.",
        "parameters": {
            "type": "object",
            "properties": {
                "target_date_str": {"type": "string", "description": "Ngày muốn xem sự kiện theo định dạng 'YYYY-MM-DD'. Bỏ trống nếu muốn xem 30 ngày tới."}
            },
            "required": []
        }
    },
    {
        "type": "function",
        "name": "create_event",
        "description": "Tạo sự kiện mới. Mặc định calendar_id để trống nếu không có.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Tiêu đề"},
                "start": {"type": "string", "description": "Format: 'YYYY-MM-DD HH:MM'"},
                "calendar_id": {"type": "string"},
                "duration_minutes": {"type": "integer", "default": 60},
                "description": {"type": "string", "default": "low"},
                "location": {"type": "string", "description": "Địa điểm sự kiện"}
            },
            "required": ["summary", "start"]
        }
    },
    {
        "type": "function",
        "name": "update_event",
        "description": "Cập nhật sự kiện. Lấy event_id từ hàm get_clean_events.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "ID chính xác của sự kiện"},
                "calendar_id": {"type": "string", "description": "ID của lịch chứa sự kiện"},
                "summary": {"type": "string", "description": "Tiêu đề sự kiện"},
                "start": {"type": "string", "description": "Format: 'YYYY-MM-DD HH:MM'"},
                "end": {"type": "string", "description": "Format: 'YYYY-MM-DD HH:MM'"},
                "description": {"type": "string", "description": "Mô tả sự kiện"},
                "location": {"type": "string", "description": "Địa điểm sự kiện"}
            },
            "required": ["event_id"]
        }
    }
]

available_functions = {
    "get_weather_forecast_data": get_weather_forecast_data,
    "get_clean_events": get_clean_events,
    "create_event": create_event,
    "list_user_calendars": list_user_calendars,
    "update_event": update_event
}