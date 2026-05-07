import os
import json
from http import HTTPStatus
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_ID = os.environ.get("BOT_ID", "8e4544bb-7da5-5531-bbd3-2b0f0b264222")
SECRET_KEY = os.environ.get("SECRET_KEY", "84303da41b94a8b489a64c7ae11759b7")
APP_ID = os.environ.get("APP_ID", "statcollection_bot")

user_states = {}

def process_message(msg_data: dict):
    chat_id = msg_data.get("chat_id", "unknown")
    bot_id = msg_data.get("bot_id")
    command = msg_data.get("body", "").strip().lower()

    if bot_id != BOT_ID:
        return {"error": "wrong bot_id"}

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
                raise ValueError("missing fields")
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
            print(f"✅ Response sent: {answer['response'][:50]}...")
        except Exception as e:
            print(f"❌ Error: {e}")
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "error": str(e)}).encode())

    def do_GET(self):
        if self.path == "/":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("🤖 statcollection_bot is alive.".encode())
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def log_message(self, format, *args):
        print(f"[HTTP] {args[0]}")

if __name__ == "__main__":
    port_env = os.environ.get("PORT")
    port = int(port_env) if port_env else 8000
    host = "0.0.0.0"
    print(f"🌱 Starting bot on {host}:{port}")
    print(f"🔍 ENV: PORT={port_env}, BOT_ID={BOT_ID[:8]}...")

    server = HTTPServer((host, port), BotHandler)
    print(f"🚀 Bot is alive at http://{host}:{port}/statcollection_bot")
    server.serve_forever()
