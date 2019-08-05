import asyncio
# from collections import deque
# from asyncio.queues import Queue


class PlotBufferManager():
    plot_buffer_map = dict()

    @staticmethod
    def add_buffer(plot_buffer):
        if plot_buffer:
            if plot_buffer.server_id not in PlotBufferManager.plot_buffer_map:
                PlotBufferManager.plot_buffer_map[plot_buffer.id] = dict()
            PlotBufferManager.plot_buffer_map[plot_buffer.server_id][plot_buffer.id] = plot_buffer
            print(f'add_buffer: {PlotBufferManager.plot_buffer_map}')

    @staticmethod
    def remove_buffer(server_id, id):
        if PlotBufferManager.get_buffer(id):
            PlotBufferManager.get_buffer(id).close()
            del PlotBufferManager.plot_buffer_map[id]
        pass
    
    @staticmethod
    def get_buffer(server_id, id):
        if server_id in PlotBufferManager.plot_buffer_map:
            if id in PlotBufferManager.plot_buffer_map[server_id]:
                return PlotBufferManager.plot_buffer_map[server_id][id]
        else:
            return None

    @staticmethod
    def stop():
        # buffer_map = PlotBufferManager.plot_buffer_map
        # print(f'stop: {buffer_map}')
        # for k, buffer in buffer_map.items():
        #     print(k, buffer)
        for server_id, v in PlotBufferManager.plot_buffer_map.items():
            for k, buffer in PlotBufferManager.plot_buffer_map[server_id].items():
                buffer.stop()


class PlotBuffer():
    def __init__(self, server_id, id, msg_buf):

        self.server_id = server_id
        self.id = id
        self.buffer = dict()
        self.msg_buf = msg_buf

        self.task_list = []
        self.task_list.append(
            asyncio.ensure_future(self.run())
        )

    def get_buffer(self):
        return list(self.buffer)

    async def run(self):

        while True:
            msg = await self.msg_buf.get()
            # print(f'listen: {msg}')
            # TODO: determine if msg is a dict. If not,
            #       turn it into one.
            self.buffer = msg

    def stop(self):
        for t in self.task_list:
            t.cancel()
