import os
import json
import datetime
import asyncio
from google import genai
from dotenv import load_dotenv
from tools_config import tools, available_functions

load_dotenv()

client_gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = "gemini-3.1-flash-lite-preview"

async def function_call_execution(channel, prompt: str):
    try:
        # Lượt 1: Gửi tin nhắn ban đầu
        interaction = await asyncio.to_thread(
            client_gemini.interactions.create,
            model=MODEL_ID,
            input=prompt,
            tools=tools,
            system_instruction=f"""Bạn là Life-OS Agent thông minh, trợ lý ảo cá nhân cho người dùng để thông báo, thêm, thay đổi thông tin sự kiện trên Google Calendar và cung cấp dữ liệu thời tiết. Hãy trả lời ngắn gọn, súc tích và ưu tiên gọi hàm khi cần thao tác với lịch hoặc thời tiết.
                                Chức năng chính của bạn là Function Call. Khi người dùng gửi yêu cầu cần gọi hàm, chú ý dùng đúng tên hàm và định dạng argument theo đúng tools.
                                Context: hôm nay là ngày {datetime.datetime.now().strftime("%d/%m/%Y")}"""
        )

        # Vòng lặp xử lý cho đến khi AI trả về Text (hết yêu cầu gọi hàm)
        while True:
            function_responses = []
            has_function_call = False

            for output in interaction.outputs:
                if output.type == "function_call":
                    has_function_call = True
                    fn_name = output.name
                    fn_args = output.arguments
                    
                    print(f"System: AI yêu cầu gọi function {fn_name} với argument {fn_args}")
                    
                    function_to_call = available_functions.get(fn_name)
                    if function_to_call:
                        # Chạy hàm thực thi (Google/Weather API) trong thread để không block bot
                        result = await asyncio.to_thread(function_to_call, **fn_args)
                        print(f"System: Kết quả hàm {fn_name}: {result}")
                        
                        # Bắt buộc kết quả hàm phải là một Dictionary (JSON Object) để API không bị nhầm lẫn
                        if not isinstance(result, dict):
                            result = {"data": result}
                            
                        function_responses.append({
                            "type": "function_result",
                            "name": fn_name,
                            "call_id": output.id,
                            "result": result
                        })
                    else:
                        await channel.send(f"⚠️ Hàm {fn_name} chưa được hỗ trợ.")

                elif hasattr(output, 'text') and output.text:
                    await channel.send(output.text)

            if not has_function_call:
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
                        input=function_responses
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