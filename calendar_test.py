# %% [Cell 1]: Import và Khởi tạo Service
import datetime
from datetime import datetime, timezone
from google_services import get_calendar_service, get_calendars # Import hàm từ file cũ của bạn

# Chạy dòng này để lấy object service mà không cần gọi API ngay
service = get_calendar_service()
print("Service đã sẵn sàng!")

# %% [Cell 2]: Gọi API và lấy Raw Data (events_result)
now = datetime.now(timezone.utc).isoformat()
print(f"TimeMin: {now}")

# Gọi API nhưng KHÔNG in ra, chỉ lưu vào biến để soi
events_result = service.events().list(
    calendarId='primary', 
    timeMin=now,
    maxResults=10, 
    singleEvents=True,
    orderBy='startTime'
).execute()

print("Đã lấy xong data. Chạy Cell dưới để soi.")

# %% [Cell 3]: Soi cấu trúc dữ liệu (Inspect)
# Tại đây bạn có thể print thử các key để xem cấu trúc JSON
print(events_result.keys())

# Lấy list sự kiện
events = events_result.get('items', [])

# In thử sự kiện đầu tiên để xem nó có những trường nào (summary, start, end, htmlLink...)
if events:
    first_event = events[0]
    print(first_event)
else:
    print("Không có sự kiện nào.")
# %%
print(events[0])  # In ra các key của sự kiện đầu tiên để xem cấu trúc chi tiết hơn
# %%
