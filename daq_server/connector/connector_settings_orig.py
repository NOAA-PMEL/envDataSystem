
'''
connector_config: 
    used to configure connector.py for communications
    that need to bridge across serial or other
    type of interface (e.g., uas payload that uses
    a serial connection from plane to groundstation where
    the server is on the uas and the ui is on the ground)
'''

connector_config = {

    'CONNECTOR_CFG': {
        
        # host, port of connector
        'connector_address': ('localhost', 9001),

        # host port of ui (django)
        'ui_address': ('192.168.86.50', 8001)
    },
    # SerialPort interface
    'IFACE_LIST': {
        "serial_usb0": {
            "INTERFACE": {
                "MODULE": "daq.interface.interface",
                "CLASS": "SerialPortInterface"
            },
            "IFCONFIG": {
                "LABEL": "serial_usb0",
                "ADDRESS": "/dev/ttyUSB0",
                "baudrate": 38400,
                # "baudrate": 115200,
                "SerialNumber": "0001"
            }
        }
    }

    # TCPPort interface 
    # 'IFACE_LIST': {
    #     "moxa_tcp_00": {
    #         "INTERFACE": {
    #             "MODULE": "daq.interface.interface",
    #             "CLASS": "TCPPortInterface"
    #         },
    #         "IFCONFIG": {
    #             "LABEL": "moxa_tcp_00",
    #             "HOST": "192.168.86.21",
    #             "PORT": "4001",
    #             "SerialNumber": "0001"
    #         }
    #     }
    # }

}
