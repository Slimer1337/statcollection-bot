import json
import os
from http import HTTPStatus
from http.server import HTTPServer, BaseHTTPRequestHandler

# === Конфигурация (берём из env) ===
BOT_ID = os.environ.get("BOT_ID", "8e4544bb-7da5-5531-bbd3-2b0f0b264222")
SECRET_KEY = os.environ.get("SECRET_KEY", "84303da41b94a8b489a64c7ae11759b7")
APP_ID = os.environ.get("APP_ID", "statcollection_bot")

# === Локальное состояние ===
user_states = {}

# === Обработка ===
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
        if self.path != "/statcollection_bot":
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)

        try:
            data = json.loads(raw_body.decode("utf-8"))
            if "chat_id" not in data or "bot_id" not in data:
                raise ValueError("missing chat_id or bot_id")
            response = process_message(data)
            answer = {
                "status": "ok",
                "response": response["body"],
                "chat_id": data["chat_id"]
            }
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
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer((host, port), BotHandler)
    print(f"🚀 Бот запущен на http://{host}:{port}/statcollection_bot")
    server.serve_forever()
