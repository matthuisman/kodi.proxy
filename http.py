#!/usr/bin/env python
import proxy

import tornado.ioloop
import tornado.web

proxy.PROXY_TYPE = proxy.HTTP

class MainHandler(tornado.web.RequestHandler):
    def get(self, url):
        result = proxy.menu(url)
        print(result)
        self.finish()

def make_app():
    return tornado.web.Application([
        (r'/(.*)', MainHandler),
    ])

if __name__ == '__main__':
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()