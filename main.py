import discord
import os
import datetime
from dotenv import load_dotenv
from discord.ext import tasks
import asyncio

from weather_service import get_weather_forecast_string
from google_services import get_upcoming_events, fetch_calendar_reminders

from keep_alive import keep_alive

# Nếu không tìm thấy file credentials.json (tức là đang chạy trên Cloud)
if not os.path.exists('credentials.json'):
    # Lấy nội dung từ biến môi trường và tạo file
    cred_data = os.getenv('GOOGLE_CREDENTIALS_JSON', '{}')
    with open('credentials.json', 'w') as f:
        f.write(cred_data)

if not os.path.exists('token.json'):
    token_data = os.getenv('GOOGLE_TOKEN_JSON', '{}')
    with open('token.json', 'w') as f:
        f.write(token_data)

# Nạp biến môi trường
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Global variable
DEFAULT_REMINDER_MINUTES = 30 # Mặc định reminder trước 30 phút
notifications_data = {}  # Reminders data holder

# Support either DISCORD_USER_ID (single or comma-separated) or DISCORD_USER_IDS
user_ids_raw = os.getenv('DISCORD_USER_ID') or os.getenv('DISCORD_USER_IDS')

if not TOKEN or not user_ids_raw:
    raise ValueError("Lỗi: Thiếu TOKEN hoặc DISCORD_USER_ID(S) trong file .env")

# Parse comma-separated IDs and coerce to ints, ignoring invalid entries
USER_IDS = []
for part in user_ids_raw.split(','):
    part = part.strip()
    if not part:
        continue
    try:
        USER_IDS.append(int(part))
    except ValueError:
        continue

if not USER_IDS:
    raise ValueError("Lỗi: Không tìm thấy USER_ID hợp lệ trong DISCORD_USER_ID(S)")

first_run = True  # Biến để kiểm tra lần chạy đầu tiên

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Cấu hình múi giờ (UTC+7)
vn_timezone = datetime.timezone(datetime.timedelta(hours=7))
run_time = datetime.time(hour=7, minute=30, second=0, tzinfo=vn_timezone)

# ---------------------------------------------------------
# ĐỊNH NGHĨA TÁC VỤ NỀN (CRONJOB) -> GỬI DM
# ---------------------------------------------------------

async def execute_briefing_logic(destination):
    """Lấy dữ liệu và gửi tin nhắn tới đích đến được chỉ định"""
    calendar_data = get_upcoming_events()
    message = f"🌅 **[Life-OS Daily Briefing]**\n\n📅 **LỊCH TRÌNH NGÀY HÔM NAY:**\n{calendar_data}"
    await destination.send(message)

@tasks.loop(time=run_time) # Hẹn giờ gửi message theo run_time
async def daily_briefing():
    for uid in USER_IDS:
        try:
            user = await client.fetch_user(uid)
            if user:
                await user.send("**🔔 Chào buổi sáng! Đây là báo cáo lịch trình và thời tiết hàng ngày của bạn.**")
                await execute_briefing_logic(user)
                await send_weather_summary(user)
                print(f"System: Đã gửi báo cáo định kỳ lịch trình và thời tiết {run_time.strftime('%H:%M')} AM cho {user.name} ({uid}).")
        except Exception as e:
            print(f"Lỗi khi gửi báo cáo cho {uid}: {e}")

def instructions():
    return (
        "🛠️ **DANH SÁCH LỆNH ĐIỀU KHIỂN:**\n"
        "▸ `!help` : Hiển thị danh sách lệnh.\n"
        "▸ `!ping` : Kiểm tra kết nối và độ trễ của Bot.\n"
        "▸ `!weather [city]` : Lấy thông tin thời tiết cho thành phố cụ thể (Mặc định: Hà Nội).\n"
        "▸ `!briefing` : Trích xuất và gửi ngay báo cáo lịch trình trong ngày hôm nay.\n"
        "▸ `!sync` : Đồng bộ thủ công reminders từ Google Calendar.\n"
        "▸ `!list` : Hiển thị danh sách các mốc nhắc nhở đang chờ.\n"
    )

# ---------------------------------------------------------
# SỰ KIỆN HỆ THỐNG
# ---------------------------------------------------------
@client.event
async def on_ready():
    global first_run
    # Đợi cho đến khi bước sang phút tiếp theo
    now = datetime.datetime.now()
    seconds_until_next_minute = 60 - now.second
    
    if seconds_until_next_minute > 0:
        print(f"System: Đang đợi {seconds_until_next_minute} giây để đồng bộ vòng lặp...")
        await asyncio.sleep(seconds_until_next_minute)
    
    print(f"System: {client.user} online.")
    if first_run:
        if not daily_briefing.is_running():
            daily_briefing.start()
            print(f"System: Cronjob lúc {run_time.strftime('%H:%M:%S')} (UTC+7) mỗi ngày.")

        if not auto_sync_task.is_running():
            auto_sync_task.start()
            print("System: Auto-sync task đã khởi động, sẽ chạy mỗi 15 phút.")

        if not check_notifications.is_running():
            check_notifications.start()
            print(f"System: {client.user} đã sẵn sàng quét thông báo.")

        try:
            for uid in USER_IDS:
                try:
                    user = await client.fetch_user(uid)
                    if user:
                        welcome_message = (
                            "🟢 **[SYSTEM ONLINE] Life-OS Agent đã khởi động thành công!**\n" # Bỏ dấu phẩy ở đây
                            f"⏰ Thông báo hàng ngày sẽ được gửi lúc {run_time.strftime('%H:%M')} sáng (UTC+7)\n\n"
                        )
                        await user.send(welcome_message)
                        await user.send(instructions())
                except Exception as e:
                    print(f"Lỗi khi gửi tin nhắn hướng dẫn cho {uid}: {e}")
        except Exception as e:
            print(f"Lỗi khi gửi tin nhắn hướng dẫn: {e}")
        
        try:
            loop = client.loop
            # Chạy hàm fetch trong thread riêng
            initial_data = await loop.run_in_executor(None, fetch_calendar_reminders, 30)
            
            # Cập nhật dữ liệu vào biến toàn cục
            notifications_data.update(initial_data)
            
            # Đếm số lượng mốc giờ (keys) có thông báo
            count = len(notifications_data)
            
            # Gửi thông báo xác nhận cho bạn qua Discord
            for uid in USER_IDS:
                user = client.get_user(uid) or await client.fetch_user(uid)
                if user:
                    await user.send(f"✅ **Đã quét lịch trình thành công!** Có `{count}` mốc thông báo sẽ được gửi trong hôm nay.")
        except Exception as e:
            print(f"⚠️ Lỗi khi quét lịch trình lần đầu: {e}")
        first_run = False       # Đánh dấu đã chạy lần đầu để tránh khởi động lại cronjob nhiều lần
    else:
        await user.send("🔄 Hệ thống vừa phục hồi sau sự cố kết nối (Reconnected).")

@client.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return

    # Command: !ping
    if message.content == '!ping':
        await message.channel.send("Pong!")

    # Command: !help
    if message.content == '!help':
        await message.channel.send(instructions())

    # Command: !weather [city]
    if message.content.startswith('!weather'):
        # Split and allow optional city argument
        parts = message.content.split(maxsplit=1)
        if len(parts) > 1:
            await send_weather_summary(message.channel, parts[1].strip())
        else:
            # Let the helper's default city value apply
            await send_weather_summary(message.channel)

    # Command: !briefing
    if message.content == '!briefing':
        await message.channel.send("🔄 Đang trích xuất dữ liệu Google Calendar...")
        try:
            # Gọi hàm logic, truyền đích đến là Channel (nơi user gõ lệnh)
            await execute_briefing_logic(message.channel)
        except Exception as e:
            await message.channel.send(f"❌ Lỗi khi lấy dữ liệu: {e}")

    # Command: !sync
    if message.content == '!sync':
        await message.channel.send("🔍 Đang quét lịch trình mới nhất...")
        global notifications_data
        
        loop = client.loop
        notifications_data = await loop.run_in_executor(None, fetch_calendar_reminders, 30)
        
        count = len(notifications_data)
        await message.channel.send(f"✅ Đồng bộ thành công! Có {count} thông báo sẽ được gửi trong hôm nay.")

    # Command: !list
    if message.content == '!list':
        if not notifications_data:
            await message.channel.send("📭 Hiện không có thông báo nào đang chờ.")
            return
            
        lines = ["📋 **Danh sách các mốc nhắc nhở đang chờ:**"]
        # Sắp xếp các mốc giờ cho dễ nhìn
        for iso_time in sorted(notifications_data.keys()):
            events = notifications_data[iso_time]
            # Lấy giờ từ chuỗi ISO để hiển thị gọn
            display_time = iso_time.split('T')[1][:5] 
            summaries = ", ".join([e['summary'] for e in events])
            lines.append(f"• `{display_time}`: {summaries}")
            
        await message.channel.send("\n".join(lines))

@tasks.loop(minutes=15)
async def auto_sync_task():
    global notifications_data
    
    # Chạy hàm fetch trong thread riêng để không treo Bot
    loop = client.loop
    updated_data = await loop.run_in_executor(None, fetch_calendar_reminders, DEFAULT_REMINDER_MINUTES)
    
    # Gộp dữ liệu mới vào dữ liệu cũ (không ghi đè hoàn toàn để tránh mất các mốc hiện tại)
    notifications_data.update(updated_data)
    print(f"Cập nhật reminders mỗi 15 phút xong. Hiện có {len(notifications_data)} mốc thông báo trong hàng đợi.")

@tasks.loop(minutes=1)
async def check_notifications():
    global notifications_data
    
    # 1. Lấy thời gian hiện tại theo phút (bỏ giây và micro giây để so sánh khớp tuyệt đối)
    now = datetime.datetime.now(vn_timezone)
    
    # Danh sách các mốc thời gian cần xóa sau khi xử lý
    to_remove = []

    # 2. Duyệt qua tất cả các mốc thông báo đang chờ
    # Chuyển thành list để tránh lỗi "dictionary changed size during iteration"
    for notify_iso, events in list(notifications_data.items()):
        try:
            # Chuyển key ISO thành đối tượng datetime để so sánh
            notify_dt = datetime.datetime.fromisoformat(notify_iso)
            
            # KIỂM TRA: Nếu thời gian hiện tại đã đến hoặc vượt quá mốc thông báo
            if now >= notify_dt:
                # Nếu thông báo quá cũ (ví dụ hơn 5 phút trước) thì chỉ xóa, không gửi để tránh làm phiền
                if (now - notify_dt).total_seconds() > 300:
                    to_remove.append(notify_iso)
                    continue

                # 3. Gửi thông báo cho tất cả người dùng trong USER_IDS
                for uid in USER_IDS:
                    try:
                        # Ưu tiên lấy từ bộ nhớ đệm (cache), nếu không thấy mới gọi API (fetch)
                        user = client.get_user(uid) or await client.fetch_user(uid)
                        if user:
                            # Tạo nội dung tin nhắn từ danh sách sự kiện tại mốc giờ này
                            message_content = format_notification_content(events)
                            await user.send(message_content)
                    except Exception as e:
                        print(f"⚠️ Lỗi gửi tin nhắn cho {uid}: {e}")
                
                # Đánh dấu đã gửi xong để xóa khỏi hàng chờ
                to_remove.append(notify_iso)

        except Exception as e:
            print(f"⚠️ Lỗi xử lý mốc thời gian {notify_iso}: {e}")

    # 4. Dọn dẹp dữ liệu trong RAM
    for iso_key in to_remove:
        notifications_data.pop(iso_key, None)

    if to_remove:
        print(f"System: Đã xử lý và dọn dẹp {len(to_remove)} mốc thông báo.")

# --- Hàm hỗ trợ định dạng tin nhắn ---
def format_notification_content(events):
    """Tạo chuỗi văn bản đẹp mắt từ danh sách sự kiện"""
    msg = "🔔 **NHẮC NHỞ LỊCH TRÌNH SẮP TỚI**\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    for ev in events:
        msg += f"📌 **{ev['summary']}**\n"
        msg += f"⏰ Bắt đầu lúc: `{ev['start']}`\n"
        if ev.get('location'):# and ev['location'] != 'Không có địa điểm':
            msg += f"📍 Địa điểm: {ev['location']}\n"
        if ev.get('description'):# and ev['description'] != 'Không có mô tả':
            msg += f"📝 Mô tả: {ev['description']}\n"
        msg += f"⏱️ Nhắc trước: {ev['reminder_minutes']} phút\n"
        msg += "────────────────────\n"
    return msg

async def send_weather_summary(target, city: str = 'hanoi'):
    """Fetches today's weather summary (blocking call run in executor)
    and sends the returned text to `target` (a Channel or User).
    """
    loop = client.loop
    # Run the blocking network call in the default executor
    summary = await loop.run_in_executor(None, get_weather_forecast_string, city)

    # Ensure we have some text to send
    if not summary:
        summary = "⚠️ Không thể lấy dữ liệu thời tiết vào lúc này."

    await target.send(summary)

keep_alive()
client.run(TOKEN)