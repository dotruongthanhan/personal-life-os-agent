from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Life-OS Bot is running 24/7!"

def run():
    # Chạy web server trên port 8080 (cổng mặc định Koyeb yêu cầu)
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()