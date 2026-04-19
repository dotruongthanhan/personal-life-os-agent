import os
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

def get_info(location: str = None):
    """
    Trả về: (local_name, lat, lon) dưới dạng tuple.
    """
    api_key = os.getenv('OPENWEATHER_API_KEY')
    search_city = location or os.getenv('CITY', 'hanoi')
    
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={search_city}&limit=1&appid={api_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            return None # Hoặc trả về (None, None, None) tùy cách bạn handle lỗi

        location_data = data[0]
        lat = location_data.get('lat')
        lon = location_data.get('lon')
        local_name = location_data.get('local_names', {}).get('vi', location_data.get('name'))
        
        return (local_name, lat, lon) # Return dạng tuple
    
    except Exception as e:
        print(f"❌ Lỗi khi lấy tọa độ: {e}")
        return None
    
def get_weather_forecast_data(location: str = None, target_date_str: str = None):
    """
    Sử dụng get_info để lấy thông tin vị trí, sau đó lấy dự báo thời tiết.
    Input: location (Tên thành phố), target_date_str (Ngày định dạng YYYY-MM-DD)
    """
    # 1. Lấy thông tin vị trí từ hàm get_info
    info = get_info(location)
    if not info:
        return []

    local_name, lat, lon = info # Unpack tuple
    
    api_key = os.getenv('OPENWEATHER_API_KEY')
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=vi"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Lấy độ lệch múi giờ của địa điểm (giây)
        tz_offset = data.get('city', {}).get('timezone', 0)
        local_tz = timezone(timedelta(seconds=tz_offset))
        
        # Thời điểm "bây giờ" tại địa điểm đó
        now_local = datetime.now(local_tz)
        today_date = now_local.date()
        
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                return {"error": "Định dạng ngày không hợp lệ. Vui lòng kiểm tra lại và sử dụng đúng định dạng 'YYYY-MM-DD'."}
        else:
            target_date = today_date
        
        if (target_date - today_date).days > 5 or (target_date - today_date).days < 0:
            return {"error": "Dữ liệu thời tiết chỉ hỗ trợ trong phạm vi 5 ngày tới kể từ hôm nay."}

        forecast_list = data.get('list', [])
        result = []

        for entry in forecast_list:
            # Lấy thời gian Unix của dự báo và chuyển sang giờ địa phương
            dt_unix = entry.get('dt')
            dt_local = datetime.fromtimestamp(dt_unix, local_tz)
            
            # ĐIỀU KIỆN LỌC: Phải khớp với target_date
            if dt_local.date() == target_date:
                # Nếu là hôm nay, chỉ lấy thời gian từ bây giờ trở đi
                if target_date == today_date and dt_local < now_local:
                    continue

                weather_info = {
                    "time": dt_local.strftime('%H:%M'),
                    "temp": entry['main'].get('temp'),
                    "description": entry['weather'][0].get('description').capitalize(),
                    "pop": entry.get('pop', 0)
                }

                # Chỉ lấy rain nếu > 0
                rain_val = entry.get('rain', {}).get('3h', 0)
                if rain_val > 0:
                    weather_info["rain"] = rain_val
                
                result.append(weather_info)
        
        return result
    
    except Exception as e:
        print(f"❌ Lỗi khi lấy dự báo thời tiết cho {local_name}: {e}")
        return []

def get_weather_forecast_string(city = None, target_date_str: str = None):
    """Lấy dự báo thời tiết các mốc giờ trong một ngày dạng string"""

    date_display = target_date_str if target_date_str else "hôm nay"
    try:
        local_name, _, _ = get_info(city)
        data = get_weather_forecast_data(city, target_date_str)
        if isinstance(data, dict) and "error" in data:
            return f"⚠️ {data['error']}"
        if not data:
            return f"⚠️ Không có dữ liệu dự báo thời tiết cho {local_name} {date_display}."
    except Exception as e:
        return f"❌ Lỗi khi lấy dữ liệu thời tiết: {e}"
    
    # Tính nhiệt độ thấp nhất và cao nhất trong ngày
    temps = [item['temp'] for item in data]
    min_t = min(temps)
    max_t = max(temps)
    forecast_lines = []

    result = f"\n🌤️ **Dự báo thời tiết {local_name} ngày {date_display}:**\n"
    result += f"🌡️ Nhiệt độ trong ngày: **{min_t}°C - {max_t}°C**\n"

    # Quét qua danh sách dự báo
    for item in data:
        time = item['time']
        temp = item['temp']
        description = item['description']
        rain_chance = int(item['pop'] * 100)
        rain_amount = item.get('rain', 0)

        summary = f"  • `{time}`: {temp}°C, {description}. Tỉ lệ mưa: {rain_chance}%"
        if rain_amount > 0:
            summary += f", lượng mưa: {rain_amount}mm."
        else:
            summary += "."
        forecast_lines.append(summary)
        
        
    result += "\n".join(forecast_lines)
    return result

def get_city_timezone(location: str = None):
    """
    Lấy múi giờ (timezone) của thành phố dựa trên OpenWeather API.
    Trả về đối tượng datetime.timezone tương ứng.
    """
    info = get_info(location)
    if not info:
        return timezone.utc  # Trả về UTC mặc định nếu có lỗi
        
    _, lat, lon = info
    api_key = os.getenv('OPENWEATHER_API_KEY')
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        tz_offset = data.get('timezone', 0)
        return timezone(timedelta(seconds=tz_offset))
    except Exception as e:
        print(f"❌ Lỗi khi lấy timezone cho thành phố: {e}")
        return timezone.utc

if __name__ == '__main__':
    print("🔄 Đang lấy dự báo thời tiết...")
    print(get_weather_forecast_string("melbounre", "2026-04-23"))