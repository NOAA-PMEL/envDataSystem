import asyncio
from asyncio.queues import Queue
from plot_server import PlotServer


class PlotManager():
    '''
    Singleton class used to access PlotServers (Bokeh Server). Multiple
    PlotServers can be managed and accessed via their host:port string as
    an id (e.g., PlotManager.get_server("localhost:5001")).
    '''
    server_map = dict()
    app_list_map = dict()

    DEFAULT_ID = ('localhost', 5001)

    @staticmethod
    def add_app(app, server_id=None, start_after_add=False):

        if not server_id:
            server_id = PlotManager.DEFAULT_ID

        server = PlotManager.get_server(server_id=server_id)

        if server and server.running:
            server.stop()

        if app:
            # fix bad name patterns
            # if app.name[0] is not '/':
            #     app.name prepend '/'
            # if there is a '/' in the rest of the name, replace with _
            server.add_app(app)

        if server and start_after_add:
            server.start()

    @staticmethod
    def add_server(config=None, server_id=None, app_list=None):

        server_id = ''
        # use config to create PlotApps
        if (config):
            pass
        elif not server_id:
            server_id = PlotManager.DEFAULT_ID

        PlotManager.server_map[server_id] = PlotServer(server_id, app_list)

    @staticmethod
    def get_server(server_id=None):
        if not server_id:
            server_id = PlotManager.DEFAULT_ID

        if server_id not in PlotManager.server_map:
            PlotManager.add_server(server_id=server_id)

        return PlotManager.server_map[server_id]

    @staticmethod
    def update_data(app_name, data, server_id=None):
        app = PlotManager.get_server(server_id=server_id).get_app(app_name)
        if app:
            app.get_app(app_name).update_data(data)
