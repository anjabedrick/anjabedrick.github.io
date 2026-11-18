"""Serves the live Framer pages from localhost so a script on the page can measure the layout
and POST the measurements back; they are saved in tools/framer-data/<slug>.json.
Run:  python3 tools/framer_proxy.py   then open http://127.0.0.1:9918/<page>"""
import http.server, os, urllib.request
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'framer-data')
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/__measure.js':  # the measuring script itself
            body = open(os.path.join(os.path.dirname(OUT), 'measure.js'), 'rb').read()
            self.send_response(200); self.send_header('Content-Type', 'text/javascript'); self.end_headers(); self.wfile.write(body); return
        url = 'https://anjabedrick.framer.website' + self.path
        try:
            body = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})).read()
        except Exception as e:
            self.send_response(502); self.end_headers(); self.wfile.write(str(e).encode()); return
        self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        n = int(self.headers['Content-Length']); body = self.rfile.read(n)
        open(os.path.join(OUT, os.path.basename(self.path.strip('/')) + '.json'), 'wb').write(body)
        self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
    def log_message(self, *a): pass
http.server.HTTPServer(('127.0.0.1', 9918), H).serve_forever()
