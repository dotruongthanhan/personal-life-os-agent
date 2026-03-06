import discord
import os
import datetime
from dotenv import load_dotenv
from discord.ext import tasks

from weather_service import get_weather_forecast_string
from google_services import get_upcoming_events

import os
import json

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
run_time = datetime.time(hour=8, minute=0, second=0, tzinfo=vn_timezone)

# ---------------------------------------------------------
# ĐỊNH NGHĨA TÁC VỤ NỀN (CRONJOB) -> GỬI DM
# ---------------------------------------------------------

async def execute_briefing_logic(destination):
    """Lấy dữ liệu và gửi tin nhắn tới đích đến được chỉ định"""
    calendar_data = get_upcoming_events()
    message = f"🌅 **[Life-OS Daily Briefing]**\n\n📅 **LỊCH TRÌNH NGÀY HÔM NAY:**\n{calendar_data}"
    await destination.send(message)

@tasks.loop(time=run_time) # Hẹn giờ gửi message lúc 8h sáng
async def daily_briefing():
    try:
        for uid in USER_IDS:
            try:
                user = await client.fetch_user(uid)
                if user:
                    await user.send("**🔔 Chào buổi sáng! Đây là báo cáo lịch trình hàng ngày của bạn.**")
                    await execute_briefing_logic(user)
                    print(f"System: Đã gửi báo cáo định kỳ 8:00 AM cho {user.name} ({uid}).")
            except Exception as e:
                print(f"Lỗi khi gửi báo cáo cho {uid}: {e}")
    except Exception as e:
        print(f"Lỗi Cronjob: {e}")

# ---------------------------------------------------------
# SỰ KIỆN HỆ THỐNG
# ---------------------------------------------------------
@client.event
async def on_ready():
    print(f"System: {client.user} online.")
    if first_run:
        if not daily_briefing.is_running():
            daily_briefing.start()
            print(f"System: Cronjob lúc {run_time.strftime('%H:%M:%S')} (UTC+7) mỗi ngày.")

        try:
            for uid in USER_IDS:
                try:
                    user = await client.fetch_user(uid)
                    if user:
                        instructions = (
                            "🟢 **[SYSTEM ONLINE] Life-OS Agent đã khởi động thành công!**\n"
                            f"⏰ Thông báo hàng ngày sẽ được gửi lúc {run_time.strftime('%H:%M:%S')} sáng (UTC+7)\n\n"
                            "🛠️ **DANH SÁCH LỆNH ĐIỀU KHIỂN:**\n"
                            "▸ `!ping` : Kiểm tra kết nối và độ trễ của Bot.\n"
                            "▸ `!weather [city]` : Lấy thông tin thời tiết cho thành phố cụ thể (Mặc định: Hà Nội).\n"
                            "▸ `!briefing` : Trích xuất và gửi ngay báo cáo lịch trình 24h tới.\n"
                        )
                        await user.send(instructions)
                except Exception as e:
                    print(f"Lỗi khi gửi tin nhắn hướng dẫn cho {uid}: {e}")
        except Exception as e:
            print(f"Lỗi khi gửi tin nhắn hướng dẫn: {e}")
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
        await message.channel.send("Pong! (DM Mode)")

    # Command: !weather [city]
    if message.content.startswith('!weather'):
        # Split and allow optional city argument
        parts = message.content.split(maxsplit=1)
        if len(parts) > 1:
            await send_weather_summary(message.channel, parts[1].strip())
        else:
            # Let the helper's default city value apply
            await send_weather_summary(message.channel)

    if message.content == '!briefing':
        await message.channel.send("🔄 Đang trích xuất dữ liệu Google Calendar...")
        try:
            # Gọi hàm logic, truyền đích đến là Channel (nơi user gõ lệnh)
            await execute_briefing_logic(message.channel)
        except Exception as e:
            await message.channel.send(f"❌ Lỗi khi lấy dữ liệu: {e}")


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