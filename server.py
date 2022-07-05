#!/usr/bin/env python
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import proxy

proxy.SETTINGS['proxy_type'] = proxy.HTTP
proxy.SETTINGS['interactive'] = False

class MainHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = self.path.lstrip('/')

        self._redirected = False
        self._lines = []

        def output_http(listitem):
            self._redirected = True
            self.send_response(302)
            self.send_header('Location', listitem.getPath().split('|')[0])
            self.end_headers()

        def _print(text):
            self._lines.append(text)

        proxy.output_http = output_http
        proxy._print = _print

        if '://' in url:
            try:
                proxy.menu(url)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write("<html><body>{}</body></html>".format(e).encode('utf8'))
            else:
                if not self._redirected:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write("<html><body>{}</body></html>".format('\n'.join(self._lines)).encode('utf8'))
        else:
            self.send_response(404)

def run(port=80):
    server_address = ('', port)
    httpd = ThreadingHTTPServer(server_address, MainHandler)
    httpd.serve_forever()

if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
