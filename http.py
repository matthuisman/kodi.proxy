#!/usr/bin/env python2
import proxy

import tornado.ioloop
import tornado.web

class MainHandler(tornado.web.RequestHandler):
    def get(self, url):
        if url.startswith('plugin://'):
            print('Calling: {}'.format(url))

            path = proxy.run(url)
            print(path)
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