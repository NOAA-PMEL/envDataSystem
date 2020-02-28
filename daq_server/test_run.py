from daq_server import DAQServer
import asyncio

server = DAQServer

event_loop = asyncio.get_event_loop()
# task = asyncio.ensure_future(heartbeat())
task_list = asyncio.Task.all_tasks()


async def heartbeat():

    while True:
        print('lub-dub')
        await asyncio.sleep(10)


def shutdown(server):
    print('shutdown:')
    # for controller in controller_list:
    #     # print(sensor)
    #     controller.stop()

    server.shutdown()
    task = asyncio.ensure_future(heartbeat())
    tasks = asyncio.Task.all_tasks()
    for t in tasks:
        # print(t)
        t.cancel()
    print("Tasks canceled")
    asyncio.get_event_loop().stop()


try:
    event_loop.run_until_complete(asyncio.wait(task_list))
except KeyboardInterrupt:
    print('closing client')
    shutdown(server)
    event_loop.run_forever()

finally:

    print('closing event loop')
    event_loop.close()
