import sys
import asyncio
from connector.connector import WSConnectorServer, WSConnectorUI


async def heartbeat():
    while True:
        print('lub-dub')
        await asyncio.sleep(10)


def main(connector_type):

    def_cfg = dict()
    def_cfg['CONNECTOR_CFG'] = {
        'connector_address': ('localhost', 9001),
        'ui_address': ('localhost', 8001)
    }
    def_cfg["IFACE_LIST"] = {

        "serial_usb0": {
            "INTERFACE": {
                "MODULE": "daq.interface.interface",
                "CLASS": "SerialPortInterface"
            },
            "IFCONFIG": {
                "LABEL": "serial_usb0",
                "ADDRESS": "/dev/ttyUSB0",
                "baudrate": 230400,
                "SerialNumber": "0001"
            }
        }
    }

    if connector_type == 'server':
        con = WSConnectorServer(
            def_cfg,
            # connector_address=('localhost', 9001),
            # ui_address=('localhost', 8001)
        )
    elif connector_type == 'ui':
        con = WSConnectorUI(
            def_cfg,
            # connector_address=('localhost', 9001),
            # ui_address=('localhost', 8001)
        )
    con.start()
    
    event_loop = asyncio.get_event_loop()
    asyncio.ensure_future(heartbeat())
    task_list = asyncio.Task.all_tasks()

    try:
        event_loop.run_until_complete(asyncio.wait(task_list))
        event_loop.run_forever()
    except KeyboardInterrupt:
        print('closing server')
        # print(f'task_list: {task_list}')
        for task in task_list:
            # print("cancel task")
            # print(f'task: {task}')
            task.cancel()

        event_loop.run_until_complete(con.shutdown())

    finally:

        print('closing event loop')
        event_loop.close()


if __name__ == "__main__":
    main(sys.argv[1])
