import os
import datetime
import asyncio
from google import genai
from dotenv import load_dotenv
from tools_config import tools, available_functions
import shared_context

load_dotenv()

client_gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = "gemini-3.1-flash-lite-preview"

async def function_call_execution(channel, prompt: str):
    try:
        now = datetime.datetime.now(shared_context.user_timezone)
        system_instruction = f"""Bạn là Life-OS Agent thông minh, trợ lý ảo cá nhân cho người dùng để thông báo, thêm, thay đổi thông tin sự kiện trên Google Calendar và cung cấp dữ liệu thời tiết. Hãy trả lời ngắn gọn, súc tích và ưu tiên gọi hàm khi cần thao tác với lịch hoặc thời tiết.
                                Chức năng chính của bạn là Function Call. Khi người dùng gửi yêu cầu cần gọi hàm, chú ý dùng đúng tên hàm và định dạng argument theo đúng tools.
                                Context: hôm nay là ngày {now.strftime("%d/%m/%Y")} và múi giờ của người dùng là {now.tzname()}."""
        # Lượt 1: Gửi tin nhắn ban đầu
        interaction = await asyncio.to_thread(
            client_gemini.interactions.create,
            model=MODEL_ID,
            input=prompt,
            tools=tools,
            system_instruction=system_instruction
        )

        # Vòng lặp xử lý cho đến khi AI trả về Text (hết yêu cầu gọi hàm)
        while True:
            function_responses = []
            has_function_call = False

            for step in interaction.steps:
                if step.type == "function_call":
                    has_function_call = True
                    fn_name = step.name
                    fn_args = step.arguments
                    
                    print(f"System: AI yêu cầu gọi function {fn_name} với argument {fn_args}")
                    
                    function_to_call = available_functions.get(fn_name)
                    if function_to_call:
                        # Chạy hàm thực thi (Google/Weather API) trong thread để không block bot
                        result = await asyncio.to_thread(function_to_call, **fn_args)
                        print(f"System: Kết quả hàm {fn_name}: {result}")
                        
                        # Bắt buộc kết quả hàm phải là một Dictionary (JSON Object) để API không bị nhầm lẫn
                        if not result: # Xử lý trường hợp kết quả rỗng (None, [], "", {})
                            result = {"message": "Không tìm thấy dữ liệu."}
                        elif not isinstance(result, dict):
                            result = {"data": result}
                            
                        function_responses.append({
                            "type": "function_result",
                            "name": fn_name,
                            "call_id": step.id,
                            "result": result
                        })
                    else:
                        await channel.send(f"⚠️ Hàm {fn_name} chưa được hỗ trợ.")

            if not has_function_call:   # Nếu không còn yêu cầu gọi hàm, gửi kết quả cuối cùng cho người dùng
                final_response = interaction.output_text or "⚠️ Không có phản hồi từ AI."
                await channel.send(final_response)
                break

            max_retries = 3
            retry_count = 0
            interaction_success = False
            
            while retry_count < max_retries and not interaction_success:
                try:
                    interaction = await asyncio.to_thread(
                        client_gemini.interactions.create,
                        model=MODEL_ID,
                        previous_interaction_id=interaction.id,
                        input=function_responses,
                        system_instruction=system_instruction
                    )
                    interaction_success = True
                except Exception as call_error:
                    retry_count += 1
                    print(f"⚠️ Lỗi API Gemini (Lần {retry_count}/{max_retries}): {call_error}")
                    if retry_count < max_retries:
                        await asyncio.sleep(2)
                        
            if not interaction_success:
                await channel.send("⚠️ Hệ thống AI đang gặp sự cố khi xử lý dữ liệu (lỗi JSON/API). Vui lòng thử lại sau.")
                break

    except Exception as e:
        await channel.send(f"⚠️ Lỗi xử lý AI: {e}")
        print(f"Full Error (Gemini): {e}")