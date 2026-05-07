# main.py — РАБОТАЮЩИЙ БЕЗ pybotx (на чистом Python)
import json
import os
import ssl
from http import HTTPStatus
from urllib.parse import parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

# === Конфигурация ===
BOT_ID = "8e4544bb-7da5-5531-bbd3-2b0f0b264222"
SECRET_KEY = "84303da41b94a8b489a64c7ae11759b7"
APP_ID = "statcollection_bot"

# === Локальное состояние (in-memory) ===
user_states = {}

# === Обработка сообщений (протокол BotX) ===
def process_message(msg_data: dict):
    chat_id = msg_data.get("chat_id", "unknown")
    bot_id = msg_data.get("bot_id")
    command = msg_data.get("body", "").strip().lower()

    if bot_id != BOT_ID:
        return {"status": "error", "error": "wrong bot_id"}

    if command == "/start":
        user_states[chat_id] = {"count": 0}
        return {"body": "👋 Привет! Я statcollection_bot. Напишите /help."}

    elif command == "/help":
        return {"body": "ℹ️ Доступно:\n/start — запустить\n/help — помощь\nЛюбой текст — эхобот."}

    elif command.startswith("/"):
        return {"body": f"Неизвестная команда: {command}. Используйте /help."}

    else:
        state = user_states.setdefault(chat_id, {"count": 0})
        state["count"] += 1
        return {"body": f"✅ Принято ({state['count']}): {msg_data.get('body', '')}"}

# === HTTP-обработчик ===
class BotHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/statcollection_bot":  # или "/statcollection_bot", уточните у админа
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)

        try:
            # Пробуем JSON
            if raw_body.startswith(b"{"):
                data = json.loads(raw_body.decode("utf-8"))
            else:
                # Если query string (редко)
                data = {k: v[0] for k, v in parse_qs(raw_body.decode()).items()}

            # Проверяем обязательные поля
            if "chat_id" not in data or "bot_id" not in data:
                raise ValueError("missing chat_id or bot_id")

            response = process_message(data)
            answer = {"status": "ok", "response": response["body"], "chat_id": data["chat_id"]}

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(answer).encode())

        except Exception as e:
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "error": str(e)}).encode())

    def log_message(self, format, *args):
        print(f"[HTTP] {args[0]}")

# === Запуск ===
if __name__ == "__main__":
    host = "0.0.0.0"   # ← ВАЖНО: Render требует слушать 0.0.0.0
    port = int(os.environ.get("PORT", 443))  # ← Render сам задаёт PORT        
    server = HTTPServer((host, port), BotHandler)
    print(f"🚀 Локальный бот запущен на http://{host}:{port}/statcollection_bot")
    print("👉 Отправьте POST /botx с JSON: {\"chat_id\": \"test\", \"bot_id\": \"8e4544bb-...\", \"body\": \"/start\"}")
    server.serve_forever()
