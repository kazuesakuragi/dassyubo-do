import http.server
import json
import os

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
EXPECTED_HEADER = "日付,商品名,カテゴリ,地域,数量,単価,売上金額"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == "/api/csvs":
            self.send_csv_list()
            return
        super().do_GET()

    def send_csv_list(self):
        names = []
        for name in sorted(os.listdir(DIRECTORY)):
            if not name.lower().endswith(".csv"):
                continue
            path = os.path.join(DIRECTORY, name)
            try:
                with open(path, encoding="utf-8") as f:
                    header = f.readline().strip()
            except (OSError, UnicodeDecodeError):
                continue
            if header == EXPECTED_HEADER:
                names.append(name)

        body = json.dumps(names, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")


if __name__ == "__main__":
    with http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"売上ダッシュボードを配信中: http://127.0.0.1:{PORT}/")
        print("Ctrl+C で停止します。")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nサーバーを停止しました。")
