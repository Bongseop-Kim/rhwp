# ponytail: PoC 정적 서버 + /log 수집, 끝나면 버린다
import http.server, sys, os

ROOT = sys.argv[1]
LOG = sys.argv[2]

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get('Content-Length', 0))).decode('utf-8', 'replace')
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(body + '\n')
        self.send_response(204)
        self.end_headers()

    def log_message(self, *a):
        pass

H.extensions_map['.wasm'] = 'application/wasm'
H.extensions_map['.mjs'] = 'text/javascript'
H.extensions_map['.js'] = 'text/javascript'
http.server.ThreadingHTTPServer(('127.0.0.1', 8765), H).serve_forever()
