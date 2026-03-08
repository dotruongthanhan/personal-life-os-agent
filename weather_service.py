import os
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

def get_weather_forecast_string(city = None):
    """Lấy dự báo thời tiết các mốc giờ trong ngày hôm nay"""
    api_key = os.getenv('OPENWEATHER_API_KEY')
    
    if city is None:
        city = os.getenv('WEATHER_CITY', 'hanoi')  # Mặc định là Hà Nội nếu không có biến môi trường

    if not api_key:
        return "⚠️ Lỗi: Thiếu OPENWEATHER_API_KEY"

    # 1. GEOCODING API
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
    
    try:
        geo_response = requests.get(geo_url)
        geo_data = geo_response.json()
        
        if geo_response.status_code != 200 or len(geo_data) == 0:
            return f"⚠️ Không tìm thấy tọa độ cho: {city}"
            
        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']
        actual_city_name = geo_data[0].get('local_names', {}).get('vi', geo_data[0]['name'])

        # 2. FORECAST API (Dự báo 3 giờ/lần)
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=vi"
        
        forecast_response = requests.get(forecast_url)
        forecast_data = forecast_response.json()
        
        if forecast_response.status_code != 200:
            return f"⚠️ Lỗi API Dự báo: {forecast_data.get('message')}"
        
        # 3. LỌC VÀ XỬ LÝ DỮ LIỆU
        # Thiết lập múi giờ Việt Nam (UTC+7)
        # Lấy độ lệch múi giờ (tính bằng giây) từ cục JSON trả về
        tz_offset_seconds = forecast_data['city']['timezone']
        
        # Tạo object timezone động dựa trên số giây đó
        city_tz = timezone(timedelta(seconds=tz_offset_seconds))
        now = datetime.now(city_tz)
        today_date = now.date()

        forecast_lines = []
        temps = []
        will_rain = False

        # Quét qua danh sách dự báo
        for item in forecast_data['list']:
            # Chuyển đổi Unix timestamp sang giờ Việt Nam
            dt_obj = datetime.fromtimestamp(item['dt'], tz=city_tz)
            
            # Chỉ lấy dữ liệu thuộc ngày hôm nay
            if dt_obj.date() == today_date:
                time_str = dt_obj.strftime('%H:%M')
                temp = round(item['main']['temp'])
                desc = item['weather'][0]['description'].capitalize()
                
                temps.append(temp)
                
                # Bắt từ khóa xem có mưa không để đưa ra lời khuyên
                if 'mưa' in desc.lower() or 'rain' in desc.lower():
                    will_rain = True

                # XÓA ĐIỀU KIỆN LỌC GIỜ, THÊM TRỰC TIẾP VÀO LIST
                forecast_lines.append(f"  • `{time_str}`: {temp}°C, {desc}")

        # 4. TỔNG HỢP THÀNH BẢN TIN
        if temps:
            min_t = min(temps)
            max_t = max(temps)
            advice = "☔ **Lưu ý: Có khả năng mưa, nhớ mang theo ô/áo mưa nhé!**" if will_rain else "😎 Thời tiết khô ráo, một ngày tuyệt vời!"
            
            result = f"\n🌤️ **Dự báo thời tiết {actual_city_name} hôm nay:**\n"
            result += f"🌡️ Nhiệt độ trong ngày: **{min_t}°C - {max_t}°C**\n"
            result += "\n".join(forecast_lines)
            result += f"\n💡 {advice}"
            
            return result
        else:
            return "⚠️ Không có dữ liệu dự báo cho thời gian còn lại trong ngày hôm nay."

    except Exception as e:
        return f"⚠️ Lỗi hệ thống thời tiết: {e}"

# if __name__ == '__main__':
#     print("🔄 Đang lấy dự báo thời tiết...")
#     print(get_weather_forecast_string("Sydney"))