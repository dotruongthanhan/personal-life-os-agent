import os
from dotenv import load_dotenv

# Tìm và nạp file .env
load_dotenv()

# Lôi key giả lập ra xem
secret_key = os.getenv("TEST_KEY")

if secret_key:
    print(f"Secret key read: {secret_key}")
else:
    print("Error: .env file cannot be found")