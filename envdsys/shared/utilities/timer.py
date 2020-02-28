import asyncio
import time


class Timer():

    def __init__(self, interval):
        self.interval = interval
        self.elapsed_time = 0
        self.timer_done = False
        self.starttime = time.time()
        self.task_list = []

        # print(self.interval)

        self.loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(self.run())
        self.task_list.append(task)

    def clean_up(self):
        for t in self.task_list:
            # print('Timer.stop():')
            # print(t)
            t.cancel()
            self.task_list.remove(t)

    def resatart(self):
        self.start()

    def start(self):
        # print('start_timer')
        self.starttime = time.time()
        self.timer_done = False

    def stop(self):
        # tasks = asyncio.Task.all_tasks()
            # tasks.remove(t)

        pass
#        tasks = asyncio.Task.all_tasks()
#        for t in self.task_list:
#            t.cancel()
#            tasks.remove(t)
#        self.is_running = False
#        self.attempt_connect = False

    async def run(self):
        while True:
            self.elapsed_time = time.time()-self.starttime
            # print(self.elapsed_time)
            # print(self.interval)
            if self.elapsed_time > self.interval:
                # print('timer went off')
                self.timer_done = True

            await asyncio.sleep(.1)
