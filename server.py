#!/usr/bin/env python3
"""QR Jigsaw server — serves the game + stores the owner's QR (POST /set-qr).
Admin (owner) sets the QR; everyone else just solves the puzzle with that QR baked in.
"""
import http.server
import socketserver
import os
import json
import base64
import urllib.parse

DIR = '/home/ubuntu/qr-puzzle'
PORT = 8899
MAX_IMG = 5 * 1024 * 1024  # 5MB

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=DIR, **kw)

    def do_POST(self):
        if self.path.startswith('/set-qr'):
            try:
                ln = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(ln)
                j = json.loads(body.decode('utf-8', 'ignore'))
                data = j.get('img', '')
                if data.startswith('data:image'):
                    b64 = data.split(',', 1)[1]
                    raw = base64.b64decode(b64)
                elif data.startswith('http://') or data.startswith('https://'):
                    # fetch remote image
                    import urllib.request
                    req = urllib.request.Request(data, headers={'User-Agent': 'Mozilla/5.0'})
                    raw = urllib.request.urlopen(req, timeout=20).read()
                else:
                    raw = data.encode('utf-8')
                if len(raw) > MAX_IMG:
                    self.respond_json(413, {'ok': False, 'err': 'image too large'})
                    return
                with open(os.path.join(DIR, 'qr.png'), 'wb') as f:
                    f.write(raw)
                print(f'[set-qr] saved {len(raw)} bytes', flush=True)
                self.respond_json(200, {'ok': True, 'bytes': len(raw)})
            except Exception as e:
                self.respond_json(400, {'ok': False, 'err': str(e)[:200]})
            return
        self.respond_json(405, {'ok': False, 'err': 'method not allowed'})

    def do_GET(self):
        # serve qr.png with no-cache so updates propagate
        if self.path.startswith('/qr.png'):
            p = os.path.join(DIR, 'qr.png')
            if os.path.exists(p):
                with open(p, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(data)
                return
            self.send_error(404)
            return
        return super().do_GET()

    def respond_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # quiet

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

if __name__ == '__main__':
    os.makedirs(DIR, exist_ok=True)
    srv = ThreadingHTTPServer(('0.0.0.0', PORT), Handler)
    print(f'QR Jigsaw server on :{PORT}', flush=True)
    srv.serve_forever()
