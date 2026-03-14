from weather_service import get_weather_forecast_data
from google_services import get_upcoming_events

tools = [
    {
        "type": "function",
        "name": "get_weather_forecast_data",
        "description": "Lấy dữ liệu dự báo thời tiết ngày hôm nay ở thành phố cụ thể.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "Thành phố hoặc tên quốc gia"}
            },
            "required": ["location"]
        }
    },
    {
        "type": "function",
        "name": "get_upcoming_events",
        "description": "Gửi thẳng output đã được format sẵn để hiển thị, không cần thêm bất kỳ giải thích nào.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]

available_functions = {
    "get_weather_forecast_data": get_weather_forecast_data,
    "get_upcoming_events": get_upcoming_events
}