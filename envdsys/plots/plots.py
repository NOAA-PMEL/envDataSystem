# import asyncio
# import json
# from asyncio.queues import Queue
from .plot_server import PlotServer
from plots.apps.plot_app import TimeSeries1D, SizeDistribution, GeoMapPlot
from django.conf import settings


class PlotManager():
    '''
    Singleton class used to access PlotServers (Bokeh Server). Multiple
    PlotServers can be managed and accessed via their host:port string as
    an id (e.g., PlotManager.get_server("localhost":5001)).
    '''
    __server_map = dict()
    __app_list_map = dict()
    __app_source_map = dict()

    # TODO: add get_default_id()

    # DEFAULT_ID = ('localhost', 5001)
    DEFAULT_ID = settings.PLOT_SERVER['server_id']

    @staticmethod
    def add_apps(config):
        # PlotManager.start_server()
        # print(f'##### add_apps -> {config}')
        server_namespace = ''
        if ("namespace") in config:
            if "daq_server" in config["namespace"]:
                server_namespace += config['namespace']['daq_server']
            if "controller" in config["namespace"]:
                server_namespace += config['namespace']['controller']
                
        if ('plot_meta' in config and 'plots' in config['plot_meta']):
            app_list = []
            for plot_name, plot_def in config['plot_meta']['plots'].items():
                # print(f'####### add_plots: {plot_name} - {plot_def}')
                if 'app_type' in plot_def:
                    if plot_def['app_type'] == 'TimeSeries1D':
                        PlotManager.add_app(
                            TimeSeries1D(
                                # config,
                                plot_def,
                                plot_name=plot_name,
                                app_name=plot_def['app_name'],
                            ),
                            start_after_add=False,
                        )
                        app_list.append(plot_def['app_name'])
                        PlotManager.register_app_source(plot_def)
                    elif plot_def['app_type'] == 'SizeDistribution':
                        # print(f'SizeDistribution add app')
                        PlotManager.add_app(
                            SizeDistribution(
                                # config,
                                plot_def,
                                plot_name=plot_name,
                                app_name=plot_def['app_name'],
                            ),
                            start_after_add=False,
                        )
                        app_list.append(plot_def['app_name'])
                        PlotManager.register_app_source(plot_def)
                    elif plot_def['app_type'] == 'GeoMapPlot':
                        # print(f'SizeDistribution add app')
                        PlotManager.add_app(
                            GeoMapPlot(
                                # config,
                                plot_def,
                                plot_name=plot_name,
                                app_name=plot_def['app_name'],
                            ),
                            start_after_add=False,
                        )
                        app_list.append(plot_def['app_name'])
                        PlotManager.register_app_source(plot_def)

            key = config['NAME']
            if 'alias' in config:
                key = config['alias']['name']
            # print(f'{app_list}, {PlotManager().__app_list_map}')
            PlotManager().__app_list_map[key] = app_list
            # print(f'{app_list}, {PlotManager().__app_list_map}')
            # PlotManager.start_server()

    @staticmethod
    def register_app_source(plot_def):
        # print(f'-=-=-= register_app_source: {plot_def}')
        if plot_def and 'source_map' in plot_def:
            for src_id, src in plot_def['source_map'].items():
                if src_id not in PlotManager().__app_source_map:
                    PlotManager().__app_source_map[src_id] = []
                app_name = plot_def['app_name']
                if app_name not in PlotManager().__app_source_map[src_id]:
                    PlotManager().__app_source_map[src_id].append(app_name)

    @staticmethod
    def get_app_list(key):
        # print(f'get_app_list: {key}, {PlotManager().__app_list_map}')
        if key in PlotManager().__app_list_map:
            return PlotManager().__app_list_map[key]

    @staticmethod
    # def add_app(
    #     app_class,
    #     config,
    #     name='',
    #     server_id=None,
    #     start_after_add=False
    # ):
    def add_app(app, server_id=None, start_after_add=True):

        # # if not in map, create app
        # print(f'add_app: {name}')
        # if app_class == 'TimeSeries1D':
        #     app = TimeSeries1D(config, name=name)

        # print(f'app = {app}')
        if not server_id:
            server_id = PlotManager.DEFAULT_ID

        server = PlotManager.get_server(server_id=server_id)
        # print(f'server = {server}')
        if server and server.running:
            server.stop()

        if app:
            # fix bad name patterns
            # if app.name[0] is not '/':
            #     app.name prepend '/'
            # if there is a '/' in the rest of the name, replace with _
            # print(f'server_add: {server}')
            server.add_app(app)

        if server and start_after_add:
            server.start()

    @staticmethod
    def start_server(server_id=None):
        PlotManager.get_server(server_id).start()

    @staticmethod
    def add_server(config=None, server_id=None, app_list=[], update=False):
        print(f'server_id: {server_id}')
        PlotManager.update_server(config=config,
                                  server_id=server_id,
                                  app_list=app_list,
                                  force=True)

    @staticmethod
    def update_server(config=None, server_id=None, app_list=None, force=False):

        # print(f'update_server: {config}, {server_id}')
        # use config to create PlotApps
        if (config):
            server_id = ''
            pass
        elif not server_id:
            server_id = PlotManager.DEFAULT_ID

        # print(f'server_id = {server_id}, {PlotManager().__server_map}')
        if (server_id in PlotManager().__server_map) or force:
            PlotManager().__server_map[server_id] = PlotServer(
                server_id, app_list)
        # print(f'server_id = {server_id}, {PlotManager().__server_map}')

    @staticmethod
    def get_server(server_id=None):
        if not server_id:
            server_id = PlotManager.DEFAULT_ID

        if server_id not in PlotManager().__server_map:
            PlotManager.add_server(server_id=server_id)

        return PlotManager().__server_map[server_id]

    @staticmethod
    async def update_data_by_source(src_id, data, server_id=None):
        # print(f'update: {src_id}')
        if src_id in PlotManager().__app_source_map:
            # print(f'    found src_id')
            server = PlotManager.get_server(server_id=server_id)
            for app_name in PlotManager().__app_source_map[src_id]:
                # print(f'        app: {app_name}')
                if server:
                    app = server.get_app(app_name)
                    if app:
                        await app.update_data(data)

    @staticmethod
    async def update_data_by_key(app_key, data, server_id=None):
        # try:
        #     data = json.loads(data_json)
        # except TypeError:
        #     print(f'invalid plot data json')
        #     return

        # print(f'update data: {app_key}, {data}')
        # print(f'app_list {PlotManager().__app_list_map}')
        for app_name in PlotManager.get_app_list(app_key):
            # print(f'app_name = {app_name}')
            app = PlotManager.get_server(server_id=server_id).get_app(app_name)
            if app:
                await app.update_data(data)
                # await asyncio.sleep(.1)

    # @staticmethod
    # async def update_data(app_name, data_json, server_id=None):
    #     try:
    #         data = json.loads(data_json)
    #     except TypeError:
    #         print(f'invalid plot data json')
    #         return

    #     # print(f'update data: {app_name}, {data}')
    #     app = PlotManager.get_server(server_id=server_id).get_app(app_name)
    #     if app:
    #         await app.update_data(data)
