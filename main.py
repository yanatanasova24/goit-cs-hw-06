import http.server
import socketserver
import socket
import threading
import os
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import json
from pymongo import MongoClient


# сервери і бази данних
PORT_HTTP = 3000
PORT_SOCKET = 5000
MONGO_URI = "mongodb://mongo:27017/"
DB_NAME = "webapp_db"
COLLECTION_NAME = "messages"
STORAGE_FILE = "storage/data.json"

# папка для json з даними
os.makedirs("storage", exist_ok=True)
if not os.path.exists(STORAGE_FILE):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

# підключення до MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# збереження у json
def save_to_local_storage(message_dict):
    data = []
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    data.append(message_dict)
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# http handler
class MyHandler(http.server.SimpleHTTPRequestHandler):

    # якщо сторінку не знайдено
    def serve_404(self):
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open("error.html", "rb") as f:
            self.wfile.write(f.read())

    # відкриття сторінок
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        if path == "/" or path == "/index.html":
            self.serve_file("index.html")
        elif path == "/message.html":
            self.serve_file("message.html")
        elif path.startswith("/style.css") or path.startswith("/logo.png"):
            self.serve_file(path[1:])
        else:
            self.serve_404()

    # відправка з форми
    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        if path in ["/send", "/message"]:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            data = parse_qs(post_data)
            username = data.get("username", [""])[0]
            message = data.get("message", [""])[0]

            message_dict = {
                "username": username,
                "message": message,
                "date": datetime.now().isoformat()
            }

            # локальне збереження
            save_to_local_storage(message_dict)

            # відправка на Socket сервер
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(("localhost", PORT_SOCKET))
                    s.sendall(json.dumps({"username": username, "message": message}).encode())
            except Exception as e:
                print("Socket Error:", e)

            self.send_response(302)
            self.send_header('Location', '/message.html')
            self.end_headers()
        else:
            self.serve_404()

    # віддати файли
    def serve_file(self, filepath, code=200):
        if not os.path.exists(filepath):
            self.serve_404()
            return
        self.send_response(code)
        if filepath.endswith(".html"):
            self.send_header('Content-type', 'text/html')
        elif filepath.endswith(".css"):
            self.send_header('Content-type', 'text/css')
        elif filepath.endswith(".png"):
            self.send_header('Content-type', 'image/png')
        self.end_headers()
        with open(filepath, "rb") as f:
            self.wfile.write(f.read())

#запустити сервер
def run_http():
    with socketserver.TCPServer(("", PORT_HTTP), MyHandler) as httpd:
        print(f"HTTP server running at http://localhost:{PORT_HTTP}")
        httpd.serve_forever()

# tcp сервер
def run_socket():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("", PORT_SOCKET))
    server.listen()
    print(f"Socket server running on port {PORT_SOCKET}")
    while True:
        conn, addr = server.accept()
        with conn:
            data = conn.recv(1024)
            if not data:
                continue
            try:
                message_dict = json.loads(data.decode())
                message_dict["date"] = datetime.now().isoformat()
                collection.insert_one(message_dict)
                print("Saved message:", message_dict)
            except Exception as e:
                print("Error:", e)

# -----------------------------
# Запуск обох серверів
# -----------------------------
if __name__ == "__main__":
    t1 = threading.Thread(target=run_http)
    t2 = threading.Thread(target=run_socket)
    t1.start()
    t2.start()
    t1.join()
    t2.join()