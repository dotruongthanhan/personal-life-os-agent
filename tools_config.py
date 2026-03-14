from weather_service import get_weather_forecast_data

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
    }
]

available_functions = {
    "get_weather_forecast_data": get_weather_forecast_data
}