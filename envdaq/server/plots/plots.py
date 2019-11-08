import asyncio
import json
from asyncio.queues import Queue
from .plot_server import PlotServer
from plots.apps.plot_app import TimeSeries1D
from django.conf import settings


class PlotManager():
    '''
    Singleton class used to access PlotServers (Bokeh Server). Multiple
    PlotServers can be managed and accessed via their host:port string as
    an id (e.g., PlotManager.get_server("localhost:5001")).
    '''
    server_map = dict()
    app_list_map = dict()

    # DEFAULT_ID = ('localhost', 5001)
    DEFAULT_ID = settings.PLOT_SERVER['server_id']

    @staticmethod
    # def add_app(
    #     app_class,
    #     config,
    #     name='',
    #     server_id=None,
    #     start_after_add=False
    # ):
    def add_app(
        app,
        server_id=None,
        start_after_add=False
    ):

        # # if not in map, create app
        # print(f'add_app: {name}')
        # if app_class == 'TimeSeries1D':
        #     app = TimeSeries1D(config, name=name)    

        print(f'app = {app}')
        if not server_id:
            server_id = PlotManager.DEFAULT_ID

        server = PlotManager.get_server(server_id=server_id)
        print(f'server = {server}')
        if server and server.running:
            server.stop()

        if app:
            # fix bad name patterns
            # if app.name[0] is not '/':
            #     app.name prepend '/'
            # if there is a '/' in the rest of the name, replace with _
            print(f'server_add: {server}')
            server.add_app(app)

        if server and start_after_add:
            server.start()

    @staticmethod
    def add_server(config=None, server_id=None, app_list=[], update=False):
        print(f'server_id: {server_id}')
        PlotManager.update_server(
            config=config,
            server_id=server_id,
            app_list=app_list,
            force=True
        )

    @staticmethod
    def update_server(config=None, server_id=None, app_list=None, force=False):

        print(f'update_server: {config}, {server_id}')
        # use config to create PlotApps
        if (config):
            server_id = ''
            pass
        elif not server_id:
            server_id = PlotManager.DEFAULT_ID
        print(f'server_id = {server_id}, {PlotManager.server_map}')
        if (server_id in PlotManager.server_map) or force:
            PlotManager.server_map[server_id] = PlotServer(server_id, app_list)
        print(f'server_id = {server_id}, {PlotManager.server_map}')

    @staticmethod
    def get_server(server_id=None):
        if not server_id:
            server_id = PlotManager.DEFAULT_ID

        if server_id not in PlotManager.server_map:
            PlotManager.add_server(server_id=server_id)

        return PlotManager.server_map[server_id]

    @staticmethod
    async def update_data(app_name, data_json, server_id=None):
        try:
            data = json.loads(data_json)
        except TypeError:
            print(f'invalid plot data json')
            return

        # print(f'update data: {app_name}, {data}')
        app = PlotManager.get_server(server_id=server_id).get_app(app_name)
        if app:
            await app.update_data(data)
