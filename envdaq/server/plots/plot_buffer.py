import asyncio
# from collections import deque
# from asyncio.queues import Queue


class PlotBufferManager():
    plot_buffer_map = dict()
    class __PlotBufferMananger():
        def __init__(self):
            self.plot_buffer_map = dict()

        def add_buffer(self, plot_buffer):
            if plot_buffer:

                print(
                    f'plot_buffer: {plot_buffer.server_id}, {plot_buffer.id}')
                # if plot_buffer.server_id not in PlotBufferManager.plot_buffer_map:
                if plot_buffer.server_id not in self.plot_buffer_map:
                    print('1')
                    # PlotBufferManager.plot_buffer_map[plot_buffer.server_id] = dict()
                    self.plot_buffer_map[plot_buffer.server_id] = dict()
                print(f'plot_buffer_map: {self.plot_buffer_map}')
                # PlotBufferManager.plot_buffer_map[plot_buffer.server_id] = {plot_buffer.id: plot_buffer}
                self.plot_buffer_map[plot_buffer.server_id][plot_buffer.id] = plot_buffer
                print(f'before add: {self.plot_buffer_map}')
                print(f'{self.plot_buffer_map[plot_buffer.server_id][plot_buffer.id]}')
                print(f'plot_buffer_map: {self.plot_buffer_map}')
                print(f'plot_buffer_map: {self.plot_buffer_map}')

        def remove_buffer(self, server_id, id):
            if self.get_buffer(server_id, id):
                self.get_buffer(server_id, id).close()
                del self.plot_buffer_map[id]
            pass

        def get_buffer(self, server_id, id):
            if server_id in self.plot_buffer_map:
                # print(f'{server_id}, {id}, {self.plot_buffer_map}')
                if id in self.plot_buffer_map[server_id]:
                    # print(
                    #     f'{self.plot_buffer_map[server_id]}, {self.plot_buffer_map[server_id][id]}'
                    # )
                    return self.plot_buffer_map[server_id][id]
            else:
                return None

        def stop(self):
            for server_id, v in self.plot_buffer_map.items():
                for k, buffer in self.plot_buffer_map[server_id].items():
                    buffer.stop()

    instance = None

    def __init__(self):
        if PlotBufferManager.instance is None:
            PlotBufferManager.instance = self.__PlotBufferMananger()

    @staticmethod
    def add_buffer(plot_buffer):
        PlotBufferManager().instance.add_buffer(plot_buffer)
        # # print(f'plot_buffer: {plot_buffer}')
        # if plot_buffer:
        #     # working = PlotBufferManager.plot_buffer_map

        #     print(f'plot_buffer: {plot_buffer.server_id}, {plot_buffer.id}')
        #     if plot_buffer.server_id not in PlotBufferManager.plot_buffer_map:
        #     # if plot_buffer.server_id not in working:
        #         print('1')
        #         PlotBufferManager.plot_buffer_map[plot_buffer.server_id] = dict()
        #         # working[plot_buffer.server_id] = dict()
        #     print(f'plot_buffer_map: {PlotBufferManager.plot_buffer_map}')
        #     PlotBufferManager.plot_buffer_map[plot_buffer.server_id] = {plot_buffer.id: plot_buffer}
        #     # working[plot_buffer.server_id] = {plot_buffer.id: plot_buffer}
        #     # print(f'working: {working}')
        #     # PlotBufferManager.plot_buffer_map = working
        #     print(f'{PlotBufferManager.plot_buffer_map[plot_buffer.server_id][plot_buffer.id]}')
        #     print(f'plot_buffer_map: {PlotBufferManager.plot_buffer_map}')

        #     print(f'add_buffer: {PlotBufferManager.plot_buffer_map}')

    @staticmethod
    def remove_buffer(server_id, id):
        PlotBufferManager().instance.remove_buffer(server_id, id)
        # if PlotBufferManager.get_buffer(id):
        #     PlotBufferManager.get_buffer(id).close()
        #     del PlotBufferManager.plot_buffer_map[id]
        # pass

    @staticmethod
    def get_buffer(server_id, id):
        return PlotBufferManager().instance.get_buffer(server_id, id)
        # if server_id in PlotBufferManager.plot_buffer_map:
        #     print(f'{server_id}, {id}, {PlotBufferManager.plot_buffer_map}')
        #     if id in PlotBufferManager.plot_buffer_map[server_id]:
        #         print(f'{PlotBufferManager.plot_buffer_map[server_id]}, {PlotBufferManager.plot_buffer_map[server_id][id]}')
        #         return PlotBufferManager.plot_buffer_map[server_id][id]
        # else:
        #     return None

    @staticmethod
    def stop():
        PlotBufferManager().instance.stop()
        # # buffer_map = PlotBufferManager.plot_buffer_map
        # # print(f'stop: {buffer_map}')
        # # for k, buffer in buffer_map.items():
        # #     print(k, buffer)
        # for server_id, v in PlotBufferManager.plot_buffer_map.items():
        #     for k, buffer in PlotBufferManager.plot_buffer_map[server_id].items():
        #         buffer.stop()


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
