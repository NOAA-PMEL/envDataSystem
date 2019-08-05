from plot_buffer import PlotBufferManager, PlotBuffer
from asyncio.queues import Queue
# import asyncio
import abc

from bokeh.plotting import figure, ColumnDataSource
from bokeh.models.widgets import TextInput, MultiSelect
from bokeh.layouts import layout
from bokeh.models import LinearAxis, Range1d


class PlotApp(abc.ABC):

    def __init__(self, config, name='/', title=''):
        self.config = config
        self.name = name
        self.title = title
        self.source = None
        self.server_id = None
        self.msg_buffer = Queue()

        # init to five minutes of data
        self.rollover = 300

        # PlotBufferManager.add_buffer(PlotBuffer('/', self.msg_buffer))
        print(f'init: {self.name}')

    @abc.abstractmethod
    def make_document(self, doc):
        pass

    def start(self, server_id):
        self.server_id = server_id
        PlotBufferManager.add_buffer(
            PlotBuffer(self.server_id, self.name, self.msg_buffer)
        )

    async def update_data(self, msg):
        await self.msg_buffer.put(msg)


class TimeSeries1D(PlotApp):
    def __init__(self, config, name='/ts_1d'):
        super().__init__(config, name=name, title='TimeSeries1D')

        # TODO: use config to define data source
        # self.source = self.configure_data_source(config)

    def make_document(self, doc):
        # self.source = ColumnDataSource({'x': [], 'y': [], 'color': []})
        # id = self.name
        source = ColumnDataSource(
            data=dict(x=[], y=[], color=[])
        )
        print(f'init: {source.data}')

        def update_source():
            # print('update_test')
            plot_buffer = PlotBufferManager.get_buffer(
                    self.server_id,
                    self.name,
                )
            if plot_buffer:
                # print(f'name: {id}, {self.name}')
                
                data_msg = plot_buffer.buffer

                # data = handle(data_msg)

                source.stream(data, rollover=self.rollover)
                # print(f'update_test: {data}')

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

            # {'x': [], 'y': [], 'color': []})
        # def update():
        #     new = {'x': [random.random()],
        #         'y': [random.random()],
        #         'color': [random.choice(['red', 'blue', 'green'])]}
        #     source.stream(new, rollover=10)
        #     # print(f'source = {source.data}')

        # doc.add_periodic_callback(update, 500)

        fig = figure(
            title=self.title,
            x_axis_type='datetime',
            #, sizing_mode='scale_width',
            # x_range=[0, 1],
            # y_range=[0, 1]
        )
        fig.line(source=source, x='x', y='y') # , color='color', size=10)

        doc.title = "Now with live updating!"
        doc.add_periodic_callback(update_source, 1000)
        # new_data = TextInput(value='')
        # new_data.on_change('value', update)

        # traces = MultiSelect(title='Traces', value=['one'], options=['one', 'two'])
        # traces.on_change('value', update_traces)
        # l = layout([
        #     [traces],
        #     [fig],
        # ])
        # doc.add_root(l)
        doc.add_root(fig)

