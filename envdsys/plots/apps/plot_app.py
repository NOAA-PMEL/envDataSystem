from plots.plot_buffer import PlotBufferManager, PlotBuffer
from asyncio.queues import Queue
from collections import deque
import asyncio
import abc
import copy
import time
import math

# import utilities.util
from datetime import datetime
from bokeh.models import Line, Circle, Legend
from bokeh.plotting import figure, ColumnDataSource
from bokeh.models.widgets import TextInput, MultiSelect
from bokeh.layouts import layout, column
from bokeh.models import LinearAxis, Range1d, DataRange1d
from bokeh.models import DatetimeTickFormatter, ColorBar
from bokeh.palettes import Spectral6
from bokeh.transform import linear_cmap
from bokeh.tile_providers import get_provider, Vendors
import json
import envdaq.util.util


class PlotApp(abc.ABC):

    def __init__(
            self,
            config,
            plot_name='default',
            app_name='/',
            title=''):

        self.config = config
        self.source_config_map = dict()
        self.name = app_name
        self.plot_name = plot_name
        self.title = title
        self.source = None
        self.sources = dict()
        self.current_data = dict()
        self.source_map = dict()
        self.server_id = None
        self.message_buffer = None
        self.msg_buffer = Queue()
        self.prefix = ''
        self.prefix_map = dict()

        # init to 60 minutes of data
        self.rollover = 3600

        self.buf_size = 100

        # PlotBufferManager.add_buffer(PlotBuffer('/', self.msg_buffer))
        print(f'init: {self.name}')

        if self.config:
            print(f'plot_app: {config}')
            self.setup()
        else:
            self.source = ColumnDataSource(
                data=dict(x=[], y=[])
            )

    @abc.abstractmethod
    def setup(self):

        # config is now just plot_def for this app and
        #  we are mapping just the source config for each source
        if self.config:
            if 'source_map' in self.config:
                for src_id, src_config in self.config['source_map'].items():
                    self.source_config_map[src_id] = src_config
                    if 'alias' in src_config:
                        self.prefix_map[src_id] = src_config['alias']['prefix']
                    else:
                        self.prefix_map[src_id] = ''

        # if config:
        #     if 'ID' in config:
        #         id = config['ID']
        #         self.config_map[id] = config
        #     # source_id = 'default'
        #     # if 'plot_meta' in config:

        #         if 'alias' in config:
        #             self.prefix_map[id] = config['alias']['prefix']
        #         else:
        #             self.prefix_map[id] = ''

    @abc.abstractmethod
    def make_document(self, doc):
        pass

    def start(self, server_id):

        self.server_id = server_id
        PlotBufferManager.add_buffer(
            PlotBuffer(
                self.server_id,
                self.name,
                self.msg_buffer,
                buf_size=self.buf_size
            )
        )
        # print(f'plot_app_buffer: {PlotBufferManager}, {PlotBufferManager.get_buffer(self.name)}')
        # print('here')

    async def update_data(self, msg):
        # print(f'update data: {msg}')
        self.update_main_source(msg)
        # await self.main_buffer.put(msg)
        await self.msg_buffer.put(msg)

    def update_main_source(self, msg):
        pass

    def handle_main(self, msg):
        pass

    def encode_data_id(self, src_id, data_name):
        return (src_id + '@' + data_name)

    def decode_data_id(self, data_id):
        parts = data_id.split('@')
        return parts[0], parts[1]

    # async def update_main_source(self):


class TimeSeries1D(PlotApp):
    def __init__(
        self,
        config,
        plot_name='default',
        app_name='/ts_1d',
        title='TimeSeries1D'
    ):

        super().__init__(
            config,
            plot_name=plot_name,
            app_name=app_name,
            title=title
        )
        print(f'TimeSeries1D init: {app_name}')
        # TODO: use config to define data source
        # self.source = self.configure_data_source(config)

    def setup(self):
        super().setup()
        print(f'TS1D:setup: {self.config}')

        # if 'ID' not in config:
        #     return
        # id = config['ID']

        # if config:
        #     if 'source_map' in config:
        #         for src_id, src_config in config['source_map'].items():
        #             self.config_map[src_id] = src_config

        # changed the json schema
        # if (
        #     'plot_meta' in config and
        #     self.plot_name in config['plot_meta']['plots']
        # ):
        #     plot = config['plot_meta']['plots'][self.plot_name]

        # self.name = self.config['plot_meta']['name']
        if self.config['app_type'] == 'TimeSeries1D':

            self.current_data['TimeSeries1D'] = dict()
            self.current_data['TimeSeries1D']['y_data'] = []

            # if plot['app_type'] == 'TimeSeries1D':
            #     self.name = plot['app_name']

            # if 'TimeSeries1D' in self.config['plot_meta']:
            #     ts1d_config = self.config['plot_meta']['TimeSeries1D']
            ts1d_config = self.config
            if 'source_map' not in ts1d_config:
                print(f'no source map in plot {self.name}')
                return

            # prefix = ''
            # if len(self.prefix_map[id]) > 0:
            #     prefix = self.prefix_map[id] + '_'

            # source_entry = dict()
            # build map
            ts1d_map = dict()
            for src_id, src in ts1d_config['source_map'].items():

                prefix = ''
                if len(self.prefix_map[src_id]) > 0:
                    prefix = self.prefix_map[src_id] + '_'

                ts1d_map[src_id] = dict()
                data = dict()

                data['datetime'] = []
                # for y in ts1d_config['y_data']:
                for y in src['y_data']:
                    name = prefix + y
                    # if len(self.prefix) > 0:
                    #     name = self.prefix + '_' + y
                    data[name] = []

                cds = ColumnDataSource(data=data)
                ts1d_map[src_id]['source'] = cds
                # print(f'*&*&* data: {data}')
                # self.source = ColumnDataSource(data=data)

                # default_data = ts1d_config['default_y_data']
                default_data = src['default_y_data']
                # print(f'default data : {default_data}')
                # self.current_data['TimeSeries1D'] = dict()
                # new_default_data = []
                for y in default_data:
                    y = prefix + y
                    # if len(self.prefix) > 0:
                    #     y = self.prefix + '_' + y
                    # new_default_data.append((src_id, y))
                    # new_default_data.append(
                    #     self.encode_data_id(src_id, y)
                    # )
                    self.current_data['TimeSeries1D']['y_data'].append(
                        self.encode_data_id(src_id, y)
                    )

                # self.current_data['TimeSeries1D']['y_data'] = (
                #     new_default_data
                # )

                # for y in ts1d_config['y_data']:
                info_map = dict()
                for y in src['y_data']:
                    meas_config = self.get_measurement_config(src_id, y)
                    # print(f'meas config = {meas_config}')
                    if meas_config:
                        units = 'counts'
                        if 'units' in meas_config:
                            units = meas_config['units']

                        color = ''
                        if 'pref_color' in meas_config:
                            color = meas_config['pref_color']

                        y = prefix + y
                        # if len(self.prefix) > 0:
                        #     y = self.prefix + '_' + y
                        # ts1d_map[y] = {
                        info_map[y] = {
                            'units': units,
                            'color': color,
                        }
                ts1d_map[src_id]['info_map'] = info_map

            self.source_map['TimeSeries1D'] = ts1d_map

            print(f'ts1d_setup source: {self.source}')
            print(f'ts1d_setup current: {self.current_data}')
            print(f'ts1d_setup map: {self.source_map}')

        # if self.config:
        #     print(f'plotapp_configure: {self.config}')

    def update_main_source(self, msg):
        # while True:
        # msg = await self.main_buffer.get()
        # print(f'TS1D: update_main_source')
        if msg:
            src_id, data = self.handle_main(msg)
            print(f'    {src_id}: {data}')
            if data:
                # print(f'data: {data}')
                # self.source.stream(data, rollover=self.rollover)
                source = self.source_map['TimeSeries1D'][src_id]['source']
                # print(f'909090  source: {source.data}, {src_id}, {data}')
                source.stream(data, rollover=self.rollover)
                # self.source_map['TimeSeries1D'][src_id]['source'].stream(
                #     data,
                #     rollover=self.rollover
                # )
                # print(f'source: {source.data}')
            # print(f'update_main_source: {self.source.data["datetime"]}')

    def handle_main(self, msg):
        data = None
        src_id = None
        # os.environ['TZ'] = 'UTC+0'
        # time.tzset()
        if 'message' in msg:
            # print(f'here:1')
            src_id = msg['message']['SENDER_ID']
            body = msg['message']['BODY']
            data = dict()
            dt_string = body['DATA']['DATETIME']
            data['datetime'] = []
            data['datetime'].append(
                envdaq.util.util.string_to_dt(dt_string),
                # datetime.strptime(dt_string, '%Y-%m-%dT%H:%M:%SZ')
                # utilities.util.string_to_dt(dt_string)
            )
            # print(data['datetime'])
            # print(f'here:1')
            source_data = self.source_map['TimeSeries1D'][src_id]['source']
            # print(f'here:2 {source_data}')
            for name, meas in body['DATA']['MEASUREMENTS'].items():
                if len(self.prefix_map[src_id]) > 0:
                    name = self.prefix_map[src_id] + '_' + name
                # if name in self.source.data:
                # print(f'    {source_data.data}')
                if name in source_data.data:
                    # print(f'        {name}: {meas["VALUE"]}')
                    data[name] = []
                    data[name].append(meas['VALUE'])
                    # data[name] = meas['VALUE']
            if len(data) == 0:
                data = None
                src_id = None

        return src_id, data

    def get_measurement_config(self, src_id, meas_name):

        if (
            src_id in self.source_config_map and
            'measurement_meta' in self.source_config_map[src_id]
        ):
            config = self.source_config_map[src_id]
            for datatype, datamap in config['measurement_meta'].items():
                if meas_name in datamap:
                    return datamap[meas_name]
        else:
            return dict()

    def get_prefix_map(self):
        return copy.deepcopy(self.prefix_map)

    def get_prefix(self):
        return self.prefix

    def get_source_map(self):
        return self.source_map

    def get_source_data(self):
        # print(f'source data: {self.source.data}')
        # return json.loads(json.dumps(self.source.data))
        return self.source.data

    def get_source_meta(self):
        return (
            copy.deepcopy(self.current_data),
            copy.deepcopy(self.source_map)
        )

    def get_rollover(self):
        return self.rollover

    def make_document(self, doc):
        # self.source = ColumnDataSource({'x': [], 'y': [], 'color': []})
        # id = self.name
        # source = ColumnDataSource(
        #     data=dict(x=[], y=[], color=[])
        # )
        # source_map = self.get_source_map()

        # source = ColumnDataSource(
        #     data=self.get_source_data()
        # )

        # TODO: instantiate ColDatSrc here
        current_data, source_map = self.get_source_meta()

        # replace ColumnDataSource in source_map with
        #   versions instantiated here. Works when deepcopy doesn't
        for src_id, src in source_map['TimeSeries1D'].items():
            if 'source' not in src:
                continue

            source_data = ColumnDataSource(
                data=src['source'].data
            )
            if source_data:
                source_map['TimeSeries1D'][src_id]['source'] = source_data

        # print(f'^^^^ {current_data}, {source_map}')
        # print(f'plot init: {source.data}')

        prefix_map = self.get_prefix_map()
        # prefix = self.get_prefix()

        rollover = self.get_rollover()

        def encode_data_id(src_id, data_name):
            return (src_id + '@' + data_name)

        def decode_data_id(data_id):
            parts = data_id.split('@')
            return parts[0], parts[1]

        def update_source():
            # print('update_test')
            plot_buffer = PlotBufferManager.get_buffer(
                self.server_id,
                self.name,
            )
            # print(f'plot buffer = {plot_buffer}, {self.server_id}, {self.name}')
            if plot_buffer and plot_buffer.has_message():
                # print(f'name: {id}, {self.name}')

                # data_msg = plot_buffer.buffer
                data_msg = plot_buffer.read()

                src_id, data = handle(data_msg)
                # print(f' update_source: {src_id}, {data}')
                if data:
                    # print(f'data[datetime] = {data["datetime"]}')
                    # print(f'232323 data: {data}')
                    # source.stream(data, rollover=self.rollover)
                    # source = source_map['TimeSeries1D'][src_id]['source']
                    # print(f' {source.data}')
                    # source.stream(data, rollover=rollover)
                    # print(f'    {source.data}')
                    source_map['TimeSeries1D'][src_id]['source'].stream(
                        data,
                        rollover=rollover
                    )
                    # print(f' update test: {source_map["TimeSeries1D"][src_id]["source"].data}')
                # print(f'update_test: {source.data["datetime"]}')

        def handle(msg):
            data = None
            src_id = None
            # os.environ['TZ'] = 'UTC+0'
            # time.tzset()
            if 'message' in msg:
                src_id = msg['message']['SENDER_ID']
                body = msg['message']['BODY']
                data = dict()
                dt_string = body['DATA']['DATETIME']
                # print(f'*****pandas: {pd.to_datetime(dt_string, format=isofmt)}')
                data['datetime'] = []
                data['datetime'].append(
                    # utilities.util.string_to_dt(dt_string).replace(tzinfo=None)
                    envdaq.util.util.string_to_dt(dt_string)

                )
                # print(data['datetime'])
                source_data = source_map['TimeSeries1D'][src_id]['source']
                # print(f'******  app update: {source_data.data}')
                for name, meas in body['DATA']['MEASUREMENTS'].items():
                    # print(f' {name}: {meas}')
                    if len(prefix_map[src_id]) > 0:
                        name = prefix_map[src_id] + '_' + name
                    # print(f'{name} in {source_data.data}')
                    if name in source_data.data:
                        data[name] = []
                        data[name].append(meas['VALUE'])
                if len(data) == 0:
                    data = None
                    src_id = None

            return src_id, data
        # def update():
        # def update_axes(number):
        #     print(f'update_axes: {number}')
        #     doc.clear()
        #     fig = figure(title='Streaming Circle Plot!', #, sizing_mode='scale_width',
        #         x_range=[0, 1], y_range=[0, 1]
        #     )
        #     fig.circle(source=source, x='x', y='y', color='color', size=10)
        #     fig.yaxis.axis_label = 'one'

        #     if number==2:
        #         fig.extra_y_ranges = {"two": Range1d(start=0, end=10)}
        #         fig.circle(source=source,  x='x', y='y', color='black', y_range_name="two")
        #         fig.add_layout(LinearAxis(y_range_name="two", axis_label='two'), 'left')

        #     l = layout([
        #         [traces],
        #         [fig],
        #     ])
        #     doc.add_root(l)

        def build_plot():
            # doc.clear()

            fig = figure(
                # title=self.title,
                x_axis_label="DateTime",
                x_axis_type="datetime",
                plot_width=600,
                plot_height=300,
                toolbar_location='above',
                # tooltips=TOOLTIPS,
                sizing_mode='stretch_width',
                # x_range=[0, 1],
                # y_range=[0, 1],

            )

            axes_map = dict()
            for trace in current_data['TimeSeries1D']['y_data']:
                # src_id = trace[0]
                # y_name = trace[1]
                src_id, y_name = decode_data_id(trace)
                # print(f'trace: {trace}, {src_id}, {y_name}')
                sm = source_map['TimeSeries1D'][src_id]
                # print(f"here1: {sm}")
                if y_name in sm['info_map']:
                    # print("here2")
                    info_map = sm['info_map'][y_name]
                    # print("here3")
                    units = info_map['units']
                    # print("here4")
                    if units not in axes_map:
                        axes_map[units] = []
                    # print("here5")
                    axes_map[units].append(trace)
                    # print("here6")

            first = True
            legend_items = []
            for axis, data in axes_map.items():
                if first:
                    for id_y in data:
                        # print(f'id_y: {id_y}')
                        # src_id = id_y[0]
                        # y_data = id_y[1]
                        src_id, y_data = decode_data_id(id_y)
                        y_source = source_map['TimeSeries1D'][src_id]['source']
                        # print(f'y_source: {y_source.data}')
                        new_line = fig.line(
                            # source=source,
                            source=y_source,
                            x='datetime',
                            y=y_data,
                            # legend=y_data,
                        )
                        legend_items.append((y_data, [new_line]))
                    fig.yaxis.axis_label = axis
                    fig.xaxis.formatter = DatetimeTickFormatter(
                        days="%F",
                        hours="%F %H:%M",
                        minutes="%F %H:%M",
                        minsec="%T",
                        seconds="%T"
                    )
                else:
                    # renders = []
                    # for y_data in data:
                    for id_y in data:
                        # src_id = id_y[0]
                        # y_data = id_y[1]
                        src_id, y_data = decode_data_id(id_y)
                        y_source = source_map['TimeSeries1D'][src_id]['source']

                        fig.extra_y_ranges[axis] = DataRange1d()
                        # axis: Range1d()}
                        new_line = Line(
                            x='datetime',
                            y=y_data,
                        )
                        render = fig.add_glyph(
                            # source,
                            y_source,
                            new_line,
                            y_range_name=axis
                        )
                        fig.extra_y_ranges[axis].renderers.append(render)
                        legend_items.append((y_data, [render]))

                        # line = fig.line(
                        #     source=source,
                        #     x='datetime',
                        #     y=y_data,
                        #     # legend=y_data,
                        #     y_range_name=axis
                        # )
                        # renders.append(line)
                    # fig.xaxis.axis_label = axis
                    fig.add_layout(LinearAxis(
                        y_range_name=axis, axis_label=axis), 'left')

                first = False
            legend = Legend(
                items=legend_items,
                location='center',
                # location=(0, -30)
            )
            fig.add_layout(legend, 'right')
            return fig

        def update_traces(attrname, old, new):
            trace_list = traces.value
            print(f'update_traces: {trace_list}')

            current_data['TimeSeries1D']['y_data'] = traces.value
            fig = build_plot()
            # doc.title = self.title
            # doc.add_periodic_callback(update_source, 1000)
            doc_layout.children[1] = fig
            # doc_layout= layout([
            #     [traces],
            #     [fig],
            # ])
            # doc.add_root(l)

            # if 'two' in trace_list:
            #     print('two axes')
            #     update_axes(2)
            # else:
            #     update_axes(1)

            # doc.clear()
            # ll = layout(
            #     [fig],
            # )
            # doc.add_root(ll)
            # new_data = {'x': data['x'], 'y': data['y'], 'color': data['color']}
            # new_data = dict(x=data['x'], y=data['y'], color=data['color'])
            # print(f'new_data: {data}')
            # new = {'x': [random.random()],
            #     'y': [random.random()],
            #     'color': [random.choice(['red', 'blue', 'green'])]}
            # source.stream(new, rollover=10)
            # try:
            #     with pull_session(url='http://localhost:5001/') as mysession:
            #         print(mysession)
            # finally:
            #     pass
            # if self.source is not None:
            #     print(f'stream: {self.source}')
            #     self.source.stream(data, rollover=10)

        TOOLTIPS = [
            ("index", "$index"),
            ("(x,y)", "($x, $y)"),
            ("desc", "@desc"),
        ]

        # fig = figure(
        #     title=self.title,
        #     x_axis_label="DateTime",
        #     x_axis_type="datetime",
        #     plot_width=600,
        #     plot_height=300,
        #     # tooltips=TOOLTIPS,
        #     # , sizing_mode='scale_width',
        #     # x_range=[0, 1],
        #     # y_range=[0, 1]
        # )
        # for trace in current_data:
        fig = build_plot()
        # fig.line(
        #     source=source,
        #     x='datetime',
        #     y='test_concentration',
        #     # legend='concentration'
        # )  # , color='color', size=10)
        # # fig.circle(source=source, x='datetime', y='concentration')

        # fig.xaxis.formatter = DatetimeTickFormatter(
        #     days="%F",
        #     hours="%F %H:%M",
        #     minutes="%F %H:%M",
        #     minsec="%T",
        #     seconds="%T"
        # )
        #     add_line(trace)
        doc.title = self.title
        # doc.add_periodic_callback(update_source, 1000)
        doc.add_periodic_callback(update_source, 250)
        # new_data = TextInput(value='')
        # new_data.on_change('value', update)

        traces_options = []
        # for name, val in source.data.items():
        for src_id, src in source_map['TimeSeries1D'].items():
            for name, val in src['source'].data.items():
                if name != "datetime":
                    # traces_options.append(((src_id, name), name))
                    option_val = encode_data_id(src_id, name)
                    traces_options.append((option_val, name))
        traces_current = current_data['TimeSeries1D']['y_data']
        # traces_current = ['test_concentration']
        # print(f'options, current: {traces_options}, {traces_current}')
        traces = MultiSelect(
            title='Select data to plot',
            value=traces_current,
            options=traces_options,
        )

        traces.on_change('value', update_traces)

        doc_layout = layout(
            [
                [traces],
                [fig],
            ],
            sizing_mode="stretch_width"
        )
        doc.add_root(doc_layout)
        # doc.add_root(fig)


class SizeDistribution(PlotApp):
    def __init__(
        self,
        config,
        plot_name='default',
        app_name='/size_dist',
        title='Size Distribution'
    ):

        super().__init__(
            config,
            plot_name=plot_name,
            app_name=app_name,
            title=title
        )
        print(f'SizeDistribution init: {app_name}')
        # TODO: use config to define data source
        # self.source = self.configure_data_source(config)

        self.buf_size = 10

    def setup(self, ):
        super().setup()
        print(f'SD:setup: {self.config}')

        # if 'ID' not in config:
        #     return
        # id = config['ID']

        # changed the json schema
        # if (
        #     'plot_meta' in self.config and
        #     self.plot_name in self.config['plot_meta']['plots']
        # ):
        #     plot = self.config['plot_meta']['plots'][self.plot_name]

        # self.name = self.config['plot_meta']['name']

        if self.config['app_type'] == 'SizeDistribution':
            # if plot['app_type'] == 'SizeDistribution':
                # self.name = plot['app_name']

                # if 'TimeSeries1D' in self.config['plot_meta']:
                #     sd_config = self.config['plot_meta']['TimeSeries1D']
                # sd_config = plot
            sd_config = self.config
            if 'source_map' not in sd_config:
                print(f'no source map in plot {self.name}')
                return

            self.current_data['SizeDistribution'] = dict()
            self.current_data['SizeDistribution']['y_data'] = []

            # data = dict()

            # prefix = ''
            # if len(self.prefix) > 0:
            #     prefix = self.prefix + '_'
            # prefix = ''
            # if len(self.prefix_map[id]) > 0:
            #     prefix = self.prefix_map[id] + '_'

            sd_map = dict()
            for src_id, src in sd_config['source_map'].items():

                prefix = ''
                if len(self.prefix_map[src_id]) > 0:
                    prefix = self.prefix_map[src_id] + '_'

                sd_map[src_id] = dict()
                data = dict()

                # data['datetime'] = []
                # for y in sd_config['y_data']:
                for y in src['y_data']:
                    name = prefix + y
                    # if len(self.prefix) > 0:
                    #     name = self.prefix + '_' + y
                    data[name] = []
                # print(f'*&*&* data: {data}')
                # self.source = ColumnDataSource(data=data)
                cds = ColumnDataSource(data=data)
                sd_map[src_id]['source'] = cds

                # default_data = sd_config['default_y_data']
                default_data = src['default_y_data']
                # print(f'default data : {default_data}')
                # self.current_data['SizeDistribution'] = dict()
                # new_default_data = []
                for y in default_data:
                    # if len(self.prefix) > 0:
                    #     y = self.prefix + '_' + y
                    #     new_default_data.append(y)
                    y = prefix + y
                    # new_default_data.append((src_id, y))
                    # new_default_data.append(
                    #     self.encode_data_id(src_id, y)
                    # )
                    self.current_data['SizeDistribution']['y_data'].append(
                        self.encode_data_id(src_id, y)
                    )
                    # print(f'new_default_data: {new_default_data}')

                # self.current_data['SizeDistribution']['y_data'] = (
                #     new_default_data
                # )
                # print(f'21212121 current data: {self.current_data}')

                # build map
                # sd_map = dict()
                info_map = dict()
                # for y in sd_config['y_data']:
                for y in src['y_data']:
                    meas_config = self.get_measurement_config(src_id, y)
                    print(f'meas Config = {meas_config}')

                    if meas_config:
                        x_axis = 'diameter'
                        if (
                            'dimensions' in meas_config and
                            'axes' in meas_config
                        ):
                            axes = meas_config['dimensions']['axes']
                            if (len(axes) > 1):
                                # assume x-axis is second dim
                                x_axis_dim = axes[1]
                                x_axis = meas_config['axes'][x_axis_dim]
                        x_axis = prefix + x_axis

                        units = 'counts'
                        if 'units' in meas_config:
                            units = meas_config['units']

                        color = ''
                        if 'pref_color' in meas_config:
                            color = meas_config['pref_color']

                        # if len(self.prefix) > 0:
                        #     y = self.prefix + '_' + y
                        y = prefix + y

                        info_map[y] = {
                            'x_axis': x_axis,
                            'units': units,
                            'color': color,
                        }
                sd_map[src_id]['info_map'] = info_map

            self.source_map['SizeDistribution'] = sd_map

            # print(f'sd_setup source: {self.source.data}')
            print(f'sd_setup current: {self.current_data}')
            print(f'sd_setup map: {self.source_map}')

        # if self.config:
        #     print(f'plotapp_configure: {self.config}')

    def update_main_source(self, msg):
        # while True:
        # msg = await self.main_buffer.get()
        if msg:
            src_id, data = self.handle_main(msg)
            if data:
                # print(f'data: {data}')
                # self.source.stream(data, rollover=self.rollover)
                # self.source.data = data
                self.source_map['SizeDistribution'][src_id]['source'].data = data
                # self.source_map['SizeDistribution'][src_id]['source'].stream(
                #     data,
                #     rollover=self.rollover
                # )

            # print(f'update_main_source: {self.source.data["datetime"]}')

    def handle_main(self, msg):
        data = None
        src_id = None
        # os.environ['TZ'] = 'UTC+0'
        # time.tzset()
        if 'message' in msg:
            # print(f'$$$$$$ @@@ {msg}')
            src_id = msg['message']['SENDER_ID']
            body = msg['message']['BODY']
            data = dict()
            # print(f'    *** handle: {src_id}, {body}')
            # dt_string = body['DATA']['DATETIME']
            # data['datetime'] = []
            # data['datetime'].append(
            #     envdaq.util.util.string_to_dt(dt_string),
            #     # datetime.strptime(dt_string, '%Y-%m-%dT%H:%M:%SZ')
            #     # utilities.util.string_to_dt(dt_string)
            # )
            # print(data['datetime'])
            source_data = self.source_map['SizeDistribution'][src_id]['source']
            # print(f'    source_data: {source_data}')
            for name, meas in body['DATA']['MEASUREMENTS'].items():
                # print(f'        {name}: {meas}')
                if len(self.prefix_map[src_id]) > 0:
                    name = self.prefix_map[src_id] + '_' + name
                # if name in self.source.data:
                # print(f'        {source_data.data}')
                if name in source_data.data:
                    # data[name] = []
                    # data[name].append(meas['VALUE'])
                    data[name] = meas['VALUE']

        # if len(data) == 0:
        #     data = None
        #     src_id = None

        return src_id, data

    def get_measurement_config(self, src_id, meas_name):

        # if 'measurement_meta' in self.config:
        #     for datatype, datamap in self.config['measurement_meta'].items():
        #         if meas_name in datamap:
        #             return datamap[meas_name]
        # else:
        #     return dict()

        if (
            src_id in self.source_config_map and
            'measurement_meta' in self.source_config_map[src_id]
        ):
            config = self.source_config_map[src_id]
            for datatype, datamap in config['measurement_meta'].items():
                if meas_name in datamap:
                    return datamap[meas_name]
        else:
            return dict()

    def get_prefix_map(self):
        return self.prefix_map

    def get_prefix(self):
        return self.prefix

    def get_source_map(self):
        return self.source_map

    def get_source_data(self):
        # print(f'source data: {self.source.data}')
        # return json.loads(json.dumps(self.source.data))
        return self.source.data

    def get_source_meta(self):
        return (
            copy.deepcopy(self.current_data),
            copy.deepcopy(self.source_map)
        )

    def make_document(self, doc):
        # self.source = ColumnDataSource({'x': [], 'y': [], 'color': []})
        # id = self.name
        # source = ColumnDataSource(
        #     data=dict(x=[], y=[], color=[])
        # )
        # source = ColumnDataSource(
        #     data=self.get_source_data()
        # )
        current_data, source_map = self.get_source_meta()
        # print(f'plot init: {source.data}')

        # replace ColumnDataSource in source_map with
        #   versions instantiated here. Works when deepcopy doesn't
        for src_id, src in source_map['SizeDistribution'].items():
            if 'source' not in src:
                continue

            source_data = ColumnDataSource(
                data=src['source'].data
            )
            if source_data:
                source_map['SizeDistribution'][src_id]['source'] = source_data

        prefix_map = self.get_prefix_map()
        # prefix = self.get_prefix()

        def encode_data_id(src_id, data_name):
            return (src_id + '@' + data_name)

        def decode_data_id(data_id):
            parts = data_id.split('@')
            return parts[0], parts[1]

        def update_source():
            # print('update_test')
            plot_buffer = PlotBufferManager.get_buffer(
                self.server_id,
                self.name,
            )
            # print(f'plot buffer = {plot_buffer}, {self.server_id}, {self.name}')
            if plot_buffer and plot_buffer.has_message():
                # print(f'name: {id}, {self.name}')
                print(
                    f'plot_buffer: {len(plot_buffer.buffer)}, {plot_buffer.buffer}')
                # data_msg = plot_buffer.buffer
                data_msg = plot_buffer.read()

                src_id, data = handle(data_msg)
                # print(f' {src_id}: {data}')
                if data:
                    # print(f'66666 update source: {data}, {source.data}')
                    # source.stream(data, rollover=self.rollover)
                    # source.stream(data, rollover=1)
                    # source.stream(data, rollover=len(data[next(iter(data))]))
                    # source.data = data
                    source = source_map['SizeDistribution'][src_id]['source']
                    # print(f'source: {source}, {self.rollover}')
                    source_map['SizeDistribution'][src_id]['source'].data = data
                    # source_map['SizeDistribution'][src_id]['source'].stream(
                    #     data,
                    #     rollover=self.rollover
                    # )
                    # source = ColumnDataSource(
                    #     data=self.get_source_data()
                    # )
                    # print(f'999999 update: {source.data}')
                # print(f'update_test: {source.data["datetime"]}')

        def handle(msg):
            data = None
            src_id = None
            # os.environ['TZ'] = 'UTC+0'
            # time.tzset()
            # print(f'handle: {msg}')
            if 'message' in msg:
                src_id = msg['message']['SENDER_ID']
                body = msg['message']['BODY']
                # print(f'    *** handle: {src_id}, {body}')
                data = dict()
                # dt_string = body['DATA']['DATETIME']
                # # print(f'*****pandas: {pd.to_datetime(dt_string, format=isofmt)}')
                # data['datetime'] = []
                # data['datetime'].append(
                #     # utilities.util.string_to_dt(dt_string).replace(tzinfo=None)
                #     envdaq.util.util.string_to_dt(dt_string)

                # )
                # print(data['datetime'])
                source_data = source_map['SizeDistribution'][src_id]['source']
                for name, meas in body['DATA']['MEASUREMENTS'].items():
                    # print('here')
                    if len(prefix_map[src_id]) > 0:
                        name = prefix_map[src_id] + '_' + name
                    # if name in source.data:
                    # print(f' {name} in {source_data.data}')
                    if name in source_data.data:
                        # print(f'22222222 data: {name}, {source.data}, {data}')
                        # data[name] = []
                        # data[name].append(meas['VALUE'])
                        data[name] = meas['VALUE']
                        # print(f'33333333 data: {name}, {source.data}, {data}')

                if len(data) == 0:
                    data = None
                    src_id = None

            return src_id, data
        # def update():
        # def update_axes(number):
        #     print(f'update_axes: {number}')
        #     doc.clear()
        #     fig = figure(title='Streaming Circle Plot!', #, sizing_mode='scale_width',
        #         x_range=[0, 1], y_range=[0, 1]
        #     )
        #     fig.circle(source=source, x='x', y='y', color='color', size=10)
        #     fig.yaxis.axis_label = 'one'

        #     if number==2:
        #         fig.extra_y_ranges = {"two": Range1d(start=0, end=10)}
        #         fig.circle(source=source,  x='x', y='y', color='black', y_range_name="two")
        #         fig.add_layout(LinearAxis(y_range_name="two", axis_label='two'), 'left')

        #     l = layout([
        #         [traces],
        #         [fig],
        #     ])
        #     doc.add_root(l)

        def build_plot():
            # doc.clear()

            fig = figure(
                # title=self.title,
                x_axis_label="Diameter",
                x_axis_type="log",
                plot_width=600,
                plot_height=300,
                toolbar_location='above',
                tooltips=TOOLTIPS,
                sizing_mode='stretch_width',
                # x_range=[0, 1],
                # y_range=[0, 1],

            )

            axes_map = dict()
            print(f'49494 current_data: {current_data}')
            for trace in current_data['SizeDistribution']['y_data']:
                # src_id = trace[0]
                # y_name = trace[1]
                src_id, y_name = decode_data_id(trace)
                sm = source_map['SizeDistribution'][src_id]
                if y_name in sm['info_map']:
                    info_map = sm['info_map'][y_name]
                    units = info_map['units']
                    # units = source_map['SizeDistribution'][trace]['units']
                    if units not in axes_map:
                        axes_map[units] = []
                    axes_map[units].append(trace)

            first = True
            legend_items = []
            # print(f'11111111111 source: {source.column_names}')
            for axis, data in axes_map.items():
                if first:
                    for id_y in data:
                        # print(f'y_data, data: {axis}, {y_data}, {data}, {source.data}')
                        # src_id = id_y[0]
                        # y_data = id_y[1]
                        src_id, y_data = decode_data_id(id_y)
                        sm = source_map['SizeDistribution'][src_id]
                        y_source = sm['source']
                        # print(f'1010101 sd: build: {y_source}, {y_data}, {sm["info_map"][y_data]["x_axis"]}')
                        new_line = fig.line(
                            source=y_source,
                            x=sm['info_map'][y_data]['x_axis'],
                            # x='msems_diameter',
                            # y='test_size_distribution',
                            y=y_data,
                            # legend=y_data,
                        )
                        new_circle = fig.circle(
                            source=y_source,
                            # x=source_map['SizeDistribution'][y_data]['x_axis'],
                            x=sm['info_map'][y_data]['x_axis'],
                            # x='msems_diameter',
                            # y='test_size_distribution',
                            y=y_data,
                            # legend=y_data,
                        )
                        legend_items.append((y_data, [new_line, new_circle]))
                    fig.yaxis.axis_label = axis
                    # fig.xaxis.formatter = DatetimeTickFormatter(
                    #     days="%F",
                    #     hours="%F %H:%M",
                    #     minutes="%F %H:%M",
                    #     minsec="%T",
                    #     seconds="%T"
                    # )
                else:
                    # renders = []

                    for id_y in data:
                        # print(f'y_data, data: {axis}, {y_data}, {data}, {source.data}')
                        # src_id = id_y[0]
                        # y_data = id_y[1]
                        src_id, y_data = decode_data_id(id_y)
                        sm = source_map['SizeDistribution'][src_id]
                        y_source = sm['source']

                        fig.extra_y_ranges[axis] = DataRange1d()
                        # axis: Range1d()}
                        new_line = Line(
                            sm['info_map'][y_data]['x_axis'],
                            # x=source_map['SizeDistribution'][y_data]['x_axis'],
                            y=y_data,
                        )
                        render = fig.add_glyph(
                            # source,
                            y_source,
                            new_line,
                            y_range_name=axis
                        )
                        fig.extra_y_ranges[axis].renderers.append(render)
                        legend_items.append((y_data, [render]))

                        # line = fig.line(
                        #     source=source,
                        #     x='datetime',
                        #     y=y_data,
                        #     # legend=y_data,
                        #     y_range_name=axis
                        # )
                        # renders.append(line)
                    # fig.xaxis.axis_label = axis
                    fig.add_layout(LinearAxis(
                        y_range_name=axis, axis_label=axis), 'left')

                first = False
            legend = Legend(
                items=legend_items,
                location='center',
                # location=(0, -30)
            )
            fig.add_layout(legend, 'right')
            return fig

        def update_traces(attrname, old, new):
            trace_list = traces.value
            print(f'update_traces: {trace_list}')

            current_data['SizeDistribution']['y_data'] = traces.value
            fig = build_plot()
            # doc.title = self.title
            # doc.add_periodic_callback(update_source, 1000)
            doc_layout.children[1] = fig

        TOOLTIPS = [
            # ("name", "$name"),
            # ("(x,y)", "($x, $y)"),
            # ("desc", "@desc"),
            ("Dp", "$x um"),
            ("N", "$y cm-3"),
        ]

        fig = build_plot()
        doc.title = self.title
        # doc.add_periodic_callback(update_source, 1000)
        doc.add_periodic_callback(update_source, 250)

        traces_options = []
        # for name, val in source.data.items():
        #     if name != "datetime":
        #         traces_options.append(name)
        for src_id, src in source_map['SizeDistribution'].items():
            for name, val in src['source'].data.items():
                if name != "datetime":
                    # traces_options.append(((src_id, name), name))
                    option = (encode_data_id(src_id, name))
                    traces_options.append((option, name))
                    # traces_options.append(name)
        traces_current = current_data['SizeDistribution']['y_data']
        traces = MultiSelect(
            title='Select data to plot',
            value=traces_current,
            options=traces_options,
        )

        traces.on_change('value', update_traces)

        doc_layout = layout(
            [
                [traces],
                [fig],
            ],
            sizing_mode="stretch_width"
        )
        # time.sleep(0.5)
        doc.add_root(doc_layout)
        # doc.add_root(fig)


class GeoMapPlot(PlotApp):
    def __init__(
        self,
        config,
        plot_name='default',
        app_name='/geomap',
        title='GeoMapPlot'
    ):

        super().__init__(
            config,
            plot_name=plot_name,
            app_name=app_name,
            title=title
        )
        print(f'GeoMapPlot init: {app_name}')
        # TODO: use config to define data source
        # self.source = self.configure_data_source(config)

    def setup(self):
        super().setup()
        print(f'GeoMap:setup: {self.config}')

        if self.config['app_type'] == 'GeoMapPlot':

            self.current_data['GeoMapPlot'] = dict()
            self.current_data['GeoMapPlot']['z_data'] = []

            # if plot['app_type'] == 'TimeSeries1D':
            #     self.name = plot['app_name']

            # if 'TimeSeries1D' in self.config['plot_meta']:
            #     ts1d_config = self.config['plot_meta']['TimeSeries1D']
            geo_config = self.config
            if 'source_map' not in geo_config:
                print(f'no source map in plot {self.name}')
                return

            # prefix = ''
            # if len(self.prefix_map[id]) > 0:
            #     prefix = self.prefix_map[id] + '_'

            # source_entry = dict()
            # build map
            geo_map = dict()
            self.sync_buffer = dict()
            self.sync_buffer['DATETIME'] = []
            self.sync_buffer['GPS'] = dict()
            self.sync_buffer['DATA'] = dict()

            for src_id, src in geo_config['source_map'].items():

                prefix = ''
                if len(self.prefix_map[src_id]) > 0:
                    prefix = self.prefix_map[src_id] + '_'

                geo_map[src_id] = dict()
                data = dict()

                data['datetime'] = []
                # data['latitude'] = []
                # data['longitude'] = []
                # data['altitude'] = []
                # for y in ts1d_config['y_data']:
                for y in src['z_data']:
                    name = prefix + y
                    # if len(self.prefix) > 0:
                    #     name = self.prefix + '_' + y
                    data[name] = []

                if 'latitude' not in data:
                    data['latitude'] = []
                if 'longitude' not in data:
                    data['longitude'] = []
                if 'altitude' not in data:
                    data['altitude'] = []

                cds = ColumnDataSource(data=data)
                geo_map[src_id]['source'] = cds

                default_data = src['default_z_data']
                # print(f'default data : {default_data}')
                # self.current_data['TimeSeries1D'] = dict()
                # new_default_data = []
                for y in default_data:
                    y = prefix + y
                    # if len(self.prefix) > 0:
                    #     y = self.prefix + '_' + y
                    # new_default_data.append((src_id, y))
                    # new_default_data.append(
                    #     self.encode_data_id(src_id, y)
                    # )
                    self.current_data['GeoMapPlot']['z_data'].append(
                        self.encode_data_id(src_id, y)
                    )

                # self.current_data['TimeSeries1D']['y_data'] = (
                #     new_default_data
                # )

                # for y in ts1d_config['y_data']:
                info_map = dict()
                for y in src['z_data']:
                    meas_config = self.get_measurement_config(src_id, y)
                    # print(f'meas config = {meas_config}')
                    if meas_config:
                        units = 'counts'
                        if 'units' in meas_config:
                            units = meas_config['units']

                        color = ''
                        if 'pref_color' in meas_config:
                            color = meas_config['pref_color']

                        y = prefix + y
                        # if len(self.prefix) > 0:
                        #     y = self.prefix + '_' + y
                        # ts1d_map[y] = {
                        info_map[y] = {
                            'units': units,
                            'color': color,
                        }
                geo_map[src_id]['info_map'] = info_map

                # setup sources to mate gps and other data
                if 'primary_gps' in src:
                    # primary_gps = src_id
                    # self.sync_buffer['GPS'][src_id] = deque(maxlen=10)
                    self.sync_buffer['GPS'][src_id] = dict()
                else:
                    # self.sync_buffer['DATA'][src_id] = deque(maxlen=10)
                    self.sync_buffer['DATA'][src_id] = dict()

            self.source_map['GeoMapPlot'] = geo_map

            print(f'geo_setup source: {self.source}')
            print(f'geo_setup current: {self.current_data}')
            print(f'geo_setup map: {self.source_map}')

        # if self.config:
        #     print(f'plotapp_configure: {self.config}')

    def update_main_source(self, msg):
        # while True:
        # msg = await self.main_buffer.get()
        # print(f'TS1D: update_main_source')
        if msg:
            # src_id, data = self.handle_main(msg)
            data_list = self.handle_main(msg)
            print(f' {data_list}')
            # print(f'    {src_id}: {data}')
            return
            if data:
                # print(f'data: {data}')
                # self.source.stream(data, rollover=self.rollover)
                source = self.source_map['TimeSeries1D'][src_id]['source']
                # print(f'909090  source: {source.data}, {src_id}, {data}')
                source.stream(data, rollover=self.rollover)
                # self.source_map['TimeSeries1D'][src_id]['source'].stream(
                #     data,
                #     rollover=self.rollover
                # )
                # print(f'source: {source.data}')
            # print(f'update_main_source: {self.source.data["datetime"]}')

    def get_sync_data(self, src_id, dt_string, msg):

        max_size = 120

        # check to see if src_id is gps
        if src_id in self.sync_buffer['GPS']:
            self.sync_buffer['GPS'][src_id][dt_string] = msg
        elif src_id in self.sync_buffer['DATA']:
            self.sync_buffer['DATA'][src_id][dt_string] = msg
        self.sync_buffer['DATETIME'].append(dt_string)

        msg_list = []
        gps_id = next(iter(self.sync_buffer['GPS']))
        gps_data = self.sync_buffer['GPS'][gps_id]
        for src_id, data in self.sync_buffer['DATA'].items():
            if (
                dt_string in data and
                dt_string in gps_data
            ):
                msg_list.append(
                    {
                        dt_string: {
                            'GPS': {
                                'src_id': gps_id,
                                'msg': gps_data
                            },
                            'DATA': {
                                'src_id': src_id,
                                'msg': data
                            }
                        }
                    }
                )

        # check for dt buffer length and trim if necessary
        if len(self.sync_buffer['DATETIME']) > max_size:
            dt = self.sync_buffer['DATETIME'][0]
            gps_id = next(iter(self.sync_buffer['GPS']))

            if dt in self.sync_buffer['GPS'][gps_id]:
                self.sync_buffer['GPS'][gps_id].pop(dt)

            for src_id, data in self.sync_buffer['DATA']:
                if dt in data:
                    data.pop(dt)

            self.sync_buffer['DATETIME'].pop(0)

        return msg_list

    def handle_main(self, msg):
        data = None
        src_id = None
        # os.environ['TZ'] = 'UTC+0'
        # time.tzset()
        if 'message' in msg:
            # print(f'here:1')
            src_id = msg['message']['SENDER_ID']
            body = msg['message']['BODY']
            data = dict()
            dt_string = body['DATA']['DATETIME']
            msg_list = self.get_sync_data(src_id, dt_string, msg)
            print(f'msg_list: {msg_list}')
            return None

            data['datetime'] = []
            data['datetime'].append(
                envdaq.util.util.string_to_dt(dt_string),
                # datetime.strptime(dt_string, '%Y-%m-%dT%H:%M:%SZ')
                # utilities.util.string_to_dt(dt_string)
            )
            # print(data['datetime'])
            # print(f'here:1')
            source_data = self.source_map['TimeSeries1D'][src_id]['source']
            # print(f'here:2 {source_data}')
            for name, meas in body['DATA']['MEASUREMENTS'].items():
                if len(self.prefix_map[src_id]) > 0:
                    name = self.prefix_map[src_id] + '_' + name
                # if name in self.source.data:
                # print(f'    {source_data.data}')
                if name in source_data.data:
                    # print(f'        {name}: {meas["VALUE"]}')
                    data[name] = []
                    data[name].append(meas['VALUE'])
                    # data[name] = meas['VALUE']
            if len(data) == 0:
                data = None
                src_id = None

        return src_id, data

    def get_measurement_config(self, src_id, meas_name):

        if (
            src_id in self.source_config_map and
            'measurement_meta' in self.source_config_map[src_id]
        ):
            config = self.source_config_map[src_id]
            for datatype, datamap in config['measurement_meta'].items():
                if meas_name in datamap:
                    return datamap[meas_name]
        else:
            return dict()

    def get_prefix_map(self):
        return copy.deepcopy(self.prefix_map)

    def get_prefix(self):
        return self.prefix

    def get_source_map(self):
        return self.source_map

    def get_source_data(self):
        # print(f'source data: {self.source.data}')
        # return json.loads(json.dumps(self.source.data))
        return self.source.data

    def get_source_meta(self):
        return (
            copy.deepcopy(self.current_data),
            copy.deepcopy(self.source_map)
        )

    def get_rollover(self):
        return self.rollover

    def make_document(self, doc):
        # self.source = ColumnDataSource({'x': [], 'y': [], 'color': []})
        # id = self.name
        # source = ColumnDataSource(
        #     data=dict(x=[], y=[], color=[])
        # )
        # source_map = self.get_source_map()

        # source = ColumnDataSource(
        #     data=self.get_source_data()
        # )

        # TODO: instantiate ColDatSrc here
        current_data, source_map = self.get_source_meta()

        # replace ColumnDataSource in source_map with
        #   versions instantiated here. Works when deepcopy doesn't
        for src_id, src in source_map['GeoMapPlot'].items():
            if 'source' not in src:
                continue

            source_data = ColumnDataSource(
                data=src['source'].data
            )
            if source_data:
                source_map['GeoMapPlot'][src_id]['source'] = source_data

        # print(f'^^^^ {current_data}, {source_map}')
        # print(f'plot init: {source.data}')

        prefix_map = self.get_prefix_map()
        # prefix = self.get_prefix()

        rollover = self.get_rollover()

        def encode_data_id(src_id, data_name):
            return (src_id + '@' + data_name)

        def decode_data_id(data_id):
            parts = data_id.split('@')
            return parts[0], parts[1]

        def update_source():
            # print('update_test')
            plot_buffer = PlotBufferManager.get_buffer(
                self.server_id,
                self.name,
            )
            # print(f'plot buffer = {plot_buffer}, {self.server_id}, {self.name}')
            if plot_buffer and plot_buffer.has_message():
                # print(f'name: {id}, {self.name}')

                # data_msg = plot_buffer.buffer
                data_msg = plot_buffer.read()

                src_id, data = handle(data_msg)
                # print(f' update_source: {src_id}, {data}')
                if data:
                    # print(f'data[datetime] = {data["datetime"]}')
                    # print(f'232323 data: {data}')
                    # source.stream(data, rollover=self.rollover)
                    # source = source_map['TimeSeries1D'][src_id]['source']
                    # print(f' {source.data}')
                    # source.stream(data, rollover=rollover)
                    # print(f'    {source.data}')
                    source_map['GeoMapPlot'][src_id]['source'].stream(
                        data,
                        rollover=rollover
                    )
                    # print(f' update test: {source_map["TimeSeries1D"][src_id]["source"].data}')
                # print(f'update_test: {source.data["datetime"]}')

        def merc(lat, lon):
            r_major = 6378137.000
            x = r_major * math.radians(lon)
            scale = x/lon
            y = 180.0/math.pi * \
                math.log(math.tan(math.pi/4.0 + lat *
                                  (math.pi/180.0)/2.0)) * scale
            return (x, y)

        def handle(msg):
            data = None
            src_id = None
            # os.environ['TZ'] = 'UTC+0'
            # time.tzset()
            if 'message' in msg:
                src_id = msg['message']['SENDER_ID']
                body = msg['message']['BODY']
                data = dict()
                dt_string = body['DATA']['DATETIME']
                # print(f'*****pandas: {pd.to_datetime(dt_string, format=isofmt)}')
                data['datetime'] = []
                data['datetime'].append(
                    # utilities.util.string_to_dt(dt_string).replace(tzinfo=None)
                    envdaq.util.util.string_to_dt(dt_string)

                )
                # print(data['datetime'])
                source_data = source_map['GeoMapPlot'][src_id]['source']
                # print(f'******  app update: {source_data.data}')
                for name, meas in body['DATA']['MEASUREMENTS'].items():
                    # print(f' {name}: {meas}')
                    if len(prefix_map[src_id]) > 0:
                        name = prefix_map[src_id] + '_' + name
                    # print(f'{name} in {source_data.data}')
                    if name in source_data.data:
                        data[name] = []
                        data[name].append(meas['VALUE'])
                if len(data) == 0:
                    data = None
                    src_id = None

            return src_id, data
        # def update():
        # def update_axes(number):
        #     print(f'update_axes: {number}')
        #     doc.clear()
        #     fig = figure(title='Streaming Circle Plot!', #, sizing_mode='scale_width',
        #         x_range=[0, 1], y_range=[0, 1]
        #     )
        #     fig.circle(source=source, x='x', y='y', color='color', size=10)
        #     fig.yaxis.axis_label = 'one'

        #     if number==2:
        #         fig.extra_y_ranges = {"two": Range1d(start=0, end=10)}
        #         fig.circle(source=source,  x='x', y='y', color='black', y_range_name="two")
        #         fig.add_layout(LinearAxis(y_range_name="two", axis_label='two'), 'left')

        #     l = layout([
        #         [traces],
        #         [fig],
        #     ])
        #     doc.add_root(l)

        def build_plot():
            # doc.clear()

            tile_provider = get_provider(Vendors.CARTODBPOSITRON)

            default_lat_range = (-85, 85)
            default_lon_range = (-180, 180)
            x_min, y_min = merc(default_lat_range[0], default_lon_range[0])
            x_max, y_max = merc(default_lat_range[1], default_lon_range[1])

            fig = figure(
                # title=self.title,
                x_range=(x_min, x_max),
                y_range=(y_min, y_max),
                x_axis_type='mercator',
                y_axis_type='mercator',
                # x_axis_label="DateTime",
                # x_axis_type="datetime",
                # plot_width=500,
                plot_height=500,
                toolbar_location='above',
                # tooltips=TOOLTIPS,
                # sizing_mode='stretch_width',
                # x_range=[0, 1],
                # y_range=[0, 1],

            )
            fig.add_tile(tile_provider)

            # axes_map = dict()
            # for trace in current_data['GeoPlotMap']['z_data']:
            #     # src_id = trace[0]
            #     # y_name = trace[1]
            #     src_id, y_name = decode_data_id(trace)
            #     # print(f'trace: {trace}, {src_id}, {y_name}')
            #     sm = source_map['GeoMapPlot'][src_id]
            #     # print(f"here1: {sm}")
            #     if y_name in sm['info_map']:
            #         # print("here2")
            #         info_map = sm['info_map'][y_name]
            #         # print("here3")
            #         units = info_map['units']
            #         # print("here4")
            #         if units not in axes_map:
            #             axes_map[units] = []
            #         # print("here5")
            #         axes_map[units].append(trace)
            #         # print("here6")

            # first = True
            # legend_items = []
            # for axis, data in axes_map.items():
            #     if first:
            #         for id_y in data:
            #             # print(f'id_y: {id_y}')
            #             # src_id = id_y[0]
            #             # y_data = id_y[1]
            #             src_id, z_data = decode_data_id(id_y)
            #             z_source = source_map['GeoMapPlot'][src_id]['source']
            #             # print(f'y_source: {y_source.data}')
            #             new_line = fig.line(
            #                 # source=source,
            #                 source=z_source,
            #                 x='longitude',
            #                 y='latitude',
            #                 line_color=mapper,
            #                 color=mapper,
            #                 # size=z_data,
            #                 # legend=y_data,
            #             )
            #             legend_items.append((z_data, [new_line]))
            #         # fig.yaxis.axis_label = axis
            #         # fig.xaxis.formatter = DatetimeTickFormatter(
            #         #     days="%F",
            #         #     hours="%F %H:%M",
            #         #     minutes="%F %H:%M",
            #         #     minsec="%T",
            #         #     seconds="%T"
            #         # )
            #     # else:
            #     #     # renders = []
            #     #     # for y_data in data:
            #     #     for id_y in data:
            #     #         # src_id = id_y[0]
            #     #         # y_data = id_y[1]
            #     #         src_id, y_data = decode_data_id(id_y)
            #     #         y_source = source_map['TimeSeries1D'][src_id]['source']

            #     #         fig.extra_y_ranges[axis] = DataRange1d()
            #     #         # axis: Range1d()}
            #     #         new_line = Line(
            #     #             x='datetime',
            #     #             y=y_data,
            #     #         )
            #     #         render = fig.add_glyph(
            #     #             # source,
            #     #             y_source,
            #     #             new_line,
            #     #             y_range_name=axis
            #     #         )
            #     #         fig.extra_y_ranges[axis].renderers.append(render)
            #     #         legend_items.append((y_data, [render]))

            #     #         # line = fig.line(
            #     #         #     source=source,
            #     #         #     x='datetime',
            #     #         #     y=y_data,
            #     #         #     # legend=y_data,
            #     #         #     y_range_name=axis
            #     #         # )
            #     #         # renders.append(line)
            #     #     # fig.xaxis.axis_label = axis
            #     #     fig.add_layout(LinearAxis(
            #     #         y_range_name=axis, axis_label=axis), 'left')

            #     first = False
            # legend = Legend(
            #     items=legend_items,
            #     location='center',
            #     # location=(0, -30)
            # )

            # # colorbar = ColorBar(color_mapper=mapper['transform'], width=8, location=(0,0))
            # # fig.add_layout(colorbar, 'right')
            # # fig.add_layout(legend, 'right')

            return fig

        def update_traces(attrname, old, new):
            trace_list = traces.value
            print(f'update_traces: {trace_list}')

            current_data['GeoMapPlot']['z_data'] = traces.value
            fig = build_plot()
            # doc.title = self.title
            # doc.add_periodic_callback(update_source, 1000)
            doc_layout.children[1] = fig
            # doc_layout= layout([
            #     [traces],
            #     [fig],
            # ])
            # doc.add_root(l)

            # if 'two' in trace_list:
            #     print('two axes')
            #     update_axes(2)
            # else:
            #     update_axes(1)

            # doc.clear()
            # ll = layout(
            #     [fig],
            # )
            # doc.add_root(ll)
            # new_data = {'x': data['x'], 'y': data['y'], 'color': data['color']}
            # new_data = dict(x=data['x'], y=data['y'], color=data['color'])
            # print(f'new_data: {data}')
            # new = {'x': [random.random()],
            #     'y': [random.random()],
            #     'color': [random.choice(['red', 'blue', 'green'])]}
            # source.stream(new, rollover=10)
            # try:
            #     with pull_session(url='http://localhost:5001/') as mysession:
            #         print(mysession)
            # finally:
            #     pass
            # if self.source is not None:
            #     print(f'stream: {self.source}')
            #     self.source.stream(data, rollover=10)

        TOOLTIPS = [
            ("index", "$index"),
            ("(x,y)", "($x, $y)"),
            ("desc", "@desc"),
        ]

        fig = build_plot()
        doc.title = self.title
        # doc.add_periodic_callback(update_source, 250)

        traces_options = []
        for src_id, src in source_map['GeoMapPlot'].items():
            for name, val in src['source'].data.items():
                if (
                    name != "latitude" and
                    name != 'longitude' and
                    name != 'altitude' and
                    name != 'datetime'
                ):
                    # traces_options.append(((src_id, name), name))
                    option_val = encode_data_id(src_id, name)
                    traces_options.append((option_val, name))
        traces_current = current_data['GeoMapPlot']['z_data']
        # traces_current = ['test_concentration']
        # print(f'options, current: {traces_options}, {traces_current}')
        traces = MultiSelect(
            title='Select data to plot',
            value=traces_current,
            options=traces_options,
        )

        # traces.on_change('value', update_traces)

        doc_layout = layout(
            [
                [traces],
                [fig],
            ],
            # sizing_mode="stretch_width"
        )
        doc.add_root(doc_layout)
        # doc.add_root(fig)
