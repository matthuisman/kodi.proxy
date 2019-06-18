#!/usr/bin/env python
import proxy

import tornado.ioloop
import tornado.web

proxy.PROXY_TYPE  = proxy.HTTP
proxy.INTERACTIVE = False

class MainHandler(tornado.web.RequestHandler):
    def get(self, url):
        def output_http(listitem):
             self.redirect(listitem.getPath(), status=302)

        proxy.output_http = output_http

        if '://' in url:
            proxy.menu(url)
        else:
            self.set_status(404)
            self.finish()

def make_app():
    return tornado.web.Application([
        (r'/(.*)', MainHandler),
    ])

if __name__ == '__main__':
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()