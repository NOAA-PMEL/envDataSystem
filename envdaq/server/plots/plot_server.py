from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler


class PlotServer():

    def __init__(self, server_id, app_list=[]):

        print(f'plotserver.init')
        self.id = server_id
        self.address = self.id[0]
        self.port = self.id[1]

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
        print(f'{self.id}, {self.app_map}')

    def add_app(self, app):
        print(f'add_app: {app}, {self.app_map}')
        if app:
            self.app_map[app.name] = app

        # if app and (app not in self.app_list):
        #     self.app_list.append(app)

    def get_app(self, app_name):
        if app_name in self.app_map:
            return self.app_map[app_name]
        else:
            return None

    def start(self):

        print(f'start server')
        app_list = []
        for name, app in self.app_map.items():
            app_list.append(app)

        for app in app_list:
            app.start(self.id)
            self.apps[app.name] = Application(
                FunctionHandler(app.make_document)
            )

        ws_origin = []
        print(f'self.id = {self.id}')
        ws_origin.append(self.address+':'+str(self.port))
        if (
            self.address != 'localhost' and
            self.address != '127.0.0.1'
        ):
            ws_origin.append('localhost:'+str(self.port))

        # add django server to ws_origin
        ws_origin.append('localhost:8001')
        print(f'{self.apps},{self.address},{self.port}')
        self.server = Server(
            self.apps,
            address=self.address,
            port=self.port,
            allow_websocket_origin=ws_origin,
        )
        self.server.start()
        if self.server:
            self.running = True
        else:
            self.running = False
