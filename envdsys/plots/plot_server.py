from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
# import asyncio


class PlotServer():
    # def __init__(self, server_id, app_list=[]):
    def __init__(self, server_id, host="localhost", port=5001, app_list=[]):

        # print(f'plotserver.init')
        self.id = server_id
        # self.address = self.id[0]
        # self.port = self.id[1]
        self.address = host
        self.port = port

        # self.app_list = []
        # self.app_list = app_list
        self.app_map = dict()
        if len(app_list) > 0:
            for app in app_list:
                self.add_app[app.name] = app

        self.task_list = []

        self.server = None
        self.running = False

        self.apps = dict()
        # print(f'{self.id}, {self.app_map}')

    def get_sig(self):
        sig = {
            "server_id": self.id,
            "host": self.address,
            "port": self.port
        }
        return sig

    def add_app(self, app):
        # print(f'add_app: {app}, {self.app_map}')
        if app:
            self.app_map[app.name] = app

        # if app and (app not in self.app_list):
        #     self.app_list.append(app)

    def get_app(self, app_name):
        if app_name in self.app_map:
            return self.app_map[app_name]
        else:
            return None

    def start(self, add_ws_origin=None):

        # if (self.running):
        #     return

        # self.stop()

        # print(f'****start server****')
        app_list = []
        for name, app in self.app_map.items():
            app_list.append(app)

        for app in app_list:
            app.start(self.id)
            self.apps[app.name] = Application(
                FunctionHandler(app.make_document))

        ws_origin = []
        ws_origin.append(self.address + ':' + str(self.port))
        if self.address != 'localhost' and self.address != '127.0.0.1':
            ws_origin.append('localhost:' + str(self.port))

        # add django server to ws_origin
        ws_origin.append('localhost:8001')
        # this is hardcoded at the moment for proxy server used in production
        ws_origin.append('localhost:8002')

        # test for docker
        ws_origin.append('*')

        # add extra ws_origin
        if add_ws_origin:
            ws_origin.append(add_ws_origin + str(self.port))

        # print(f'------- {self.apps},{self.address},{self.port}')
        self.server = Server(
            self.apps,
            address=self.address,
            # address="0.0.0.0",
            port=self.port,
            allow_websocket_origin=ws_origin,
        )
        self.server.start()
        if self.server:
            self.running = True
            print(f'Started Plot Server: {self.address}:{self.port}')
        else:
            self.running = False

    def stop(self, wait=True):
        if self.server:
            for name, app in self.app_map.items():
                app.stop(self.id)

            self.server.unlisten()
            self.server.stop(wait)
            self.server = None
            # self.server.io_loop.close()
