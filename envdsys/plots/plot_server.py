from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler


class PlotServer():

    def __init__(self, server_id, app_list=[]):

        self.id = server_id
        self.address = self.server_id[0]
        self.port = self.server_id[1]

        self.app_list = app_list

        self.task_list = []

        self.server = None
        self.running = False

        self.apps = dict()

    def add_app(self, app):
        if app:
            self.app_list.append(app)

    def start(self):

        for app in self.app_list:
            app.start(self.id)
            self.apps[app.id] = Application(
                FunctionHandler(app.make_document)
            )

        ws_origin = []
        ws_origin.append(self.address+':'+str(self.port))
        if self.address != 'localhost' and self.address != '127.0.0.1':
            ws_origin.append('localhost:'+str(self.port))
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
