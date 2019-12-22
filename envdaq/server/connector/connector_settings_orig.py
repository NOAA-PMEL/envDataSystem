
connector_config = {

    'CONNECTOR_CFG': {
        'connector_address': ('localhost', 9001),
        'ui_address': ('localhost', 8001)
    },
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
                "SerialNumber": "0001"
            }
        }
    }
}
