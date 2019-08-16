from plots.plot_buffer import PlotBufferManager, PlotBuffer
from asyncio.queues import Queue
import asyncio
import abc

import utilities.util

from bokeh.plotting import figure, ColumnDataSource
from bokeh.models.widgets import TextInput, MultiSelect
from bokeh.layouts import layout
from bokeh.models import LinearAxis, Range1d
from bokeh.models import DatetimeTickFormatter
import json


class PlotApp(abc.ABC):

    def __init__(self, config, name='/', title=''):
        self.config = config
        self.name = name
        self.title = title
        self.source = None
        self.current_data = dict()
        self.source_map = dict()
        self.server_id = None
        self.message_buffer = None
        self.msg_buffer = Queue()

        # init to 60 minutes of data
        self.rollover = 3600

        # PlotBufferManager.add_buffer(PlotBuffer('/', self.msg_buffer))
        print(f'init: {self.name}')

        if self.config:
            self.setup()
        else:
            self.source = ColumnDataSource(
                data=dict(x=[], y=[])
            )

    @abc.abstractmethod
    def setup(self):
        pass

    @abc.abstractmethod
    def make_document(self, doc):
        pass

    def start(self, server_id):

        self.server_id = server_id
        PlotBufferManager.add_buffer(
            PlotBuffer(self.server_id, self.name, self.msg_buffer)
        )

    async def update_data(self, msg):
        # print(f'update data: {msg}')
        self.update_main_source(msg)
        # await self.main_buffer.put(msg)
        await self.msg_buffer.put(msg)

    # async def update_main_source(self):
    def update_main_source(self, msg):
        # while True:
        # msg = await self.main_buffer.get()
        if msg:
            data = self.handle_main(msg)
            if data:
                # print(f'data: {data}')
                self.source.stream(data, rollover=self.rollover)
            # print(f'update_main_source: {self.source.data["datetime"]}')

    def handle_main(self, msg):
        data = None
        # os.environ['TZ'] = 'UTC+0'
        # time.tzset()
        if 'message' in msg:
            body = msg['message']['BODY']
            data = dict()
            dt_string = body['DATA']['DATETIME']
            data['datetime'] = []
            data['datetime'].append(
                utilities.util.string_to_dt(dt_string)
            )
            # print(data['datetime'])
            for name, meas in body['DATA']['MEASUREMENTS'].items():
                if name in self.source.data:
                    data[name] = []
                    data[name].append(meas['VALUE'])
        return data


class TimeSeries1D(PlotApp):
    def __init__(self, config, name='/ts_1d', title='TimeSeries1D'):
        super().__init__(config, name=name, title=title)
        print(f'TimeSeries1D init: {name}')
        # TODO: use config to define data source
        # self.source = self.configure_data_source(config)

    def setup(self):
        super().setup()
        print(f'TS1D:setup: {self.config}')

        if 'plot_meta' in self.config:
            self.name = self.config['plot_meta']['name']

            if 'TimeSeries1D' in self.config['plot_meta']:
                ts1d_config = self.config['plot_meta']['TimeSeries1D']
                data = dict()
                data['datetime'] = []
                for y in ts1d_config['y_data']:
                    data[y] = []
                self.source = ColumnDataSource(data=data)

                default_data = ts1d_config['default_y_data']
                self.current_data['TimeSeries1D'] = dict()
                self.current_data['TimeSeries1D']['y_data'] = default_data

                # build map
                ts1d_map = dict()
                for y in ts1d_config['y_data']:
                    meas_config = self.get_measurement_config(y)
                    units = 'counts'
                    if 'units' in meas_config:
                        units = meas_config['units']

                    color = ''
                    if 'pref_color' in meas_config:
                        color = meas_config['pref_color']

                    ts1d_map[y] = {
                        'units': units,
                        'color': color,
                    }
                self.source_map['TimeSeries1D'] = ts1d_map

                print(f'ts1d_setup source: {self.source}')
                print(f'ts1d_setup current: {self.current_data}')
                print(f'ts1d_setup map: {self.source_map}')

        # if self.config:
        #     print(f'plotapp_configure: {self.config}')

    def get_measurement_config(self, meas_name):

        if 'measurement_meta' in self.config:
            for datatype, datamap in self.config['measurement_meta'].items():
                if meas_name in datamap:
                    return datamap[meas_name]
        else:
            return dict()

    def get_source_data(self):
        print(f'source data: {self.source.data}')
        # return json.loads(json.dumps(self.source.data))
        return self.source.data

    def get_source_meta(self):
        return self.current_data, self.source_map

    def make_document(self, doc):
        # self.source = ColumnDataSource({'x': [], 'y': [], 'color': []})
        # id = self.name
        # source = ColumnDataSource(
        #     data=dict(x=[], y=[], color=[])
        # )
        source = ColumnDataSource(
            data=self.get_source_data()
        )
        current_data, source_map = self.get_source_meta()
        # print(f'plot init: {source.data}')

        def update_source():
            # print('update_test')
            plot_buffer = PlotBufferManager.get_buffer(
                self.server_id,
                self.name,
            )
            # print(f'plot buffer = {plot_buffer}')
            if plot_buffer:
                # print(f'name: {id}, {self.name}')

                data_msg = plot_buffer.buffer

                data = handle(data_msg)
                if data:
                    # print(f'data: {data}')
                    source.stream(data, rollover=self.rollover)
                # print(f'update_test: {source.data["datetime"]}')

        def handle(msg):
            data = None
            # os.environ['TZ'] = 'UTC+0'
            # time.tzset()
            if 'message' in msg:
                body = msg['message']['BODY']
                data = dict()
                dt_string = body['DATA']['DATETIME']
                # print(f'*****pandas: {pd.to_datetime(dt_string, format=isofmt)}')
                data['datetime'] = []
                data['datetime'].append(
                    # utilities.util.string_to_dt(dt_string).replace(tzinfo=None)
                    utilities.util.string_to_dt(dt_string)
                )
                # print(data['datetime'])
                for name, meas in body['DATA']['MEASUREMENTS'].items():
                    if name in source.data:
                        data[name] = []
                        data[name].append(meas['VALUE'])
            return data
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

        # def update_traces(attrname, old, new):
        #     trace_list = traces.value
        #     print(f'update_traces: {trace_list}')
        #     if 'two' in trace_list:
        #         print('two axes')
        #         update_axes(2)
        #     else:
        #         update_axes(1)

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

        fig = figure(
            title=self.title,
            x_axis_label="DateTime",
            x_axis_type="datetime",
            # , sizing_mode='scale_width',
            # x_range=[0, 1],
            # y_range=[0, 1]
        )
        # for trace in current_data:
        #     add_line(trace)

        fig.line(source=source, x='datetime', y='concentration')  # , color='color', size=10)
        # fig.circle(source=source, x='datetime', y='concentration')
        
        fig.xaxis.formatter = DatetimeTickFormatter(
            days="%F",
            hours="%F %H:%M",
            minutes="%F %H:%M",
            minsec="%T",
            seconds="%T"
        )
        doc.title = self.title
        doc.add_periodic_callback(update_source, 1000)
        # new_data = TextInput(value='')
        # new_data.on_change('value', update)

        traces_options = []
        for name, val in source.data.items():
            if name != "datetime":
                traces_options.append(name)
        traces_current = current_data['TimeSeries1D']['y_data']
        traces = MultiSelect(
            title='Select data to plot',
            value=traces_current,
            options=traces_options
        )
        # traces.on_change('value', update_traces)
        l = layout([
            [traces],
            [fig],
        ])
        doc.add_root(l)
        # doc.add_root(fig)
