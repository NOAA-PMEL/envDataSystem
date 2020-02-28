dummy1_iface_cfg = {
    'INTERFACE': {
        'MODULE': 'daq.interface.interface',
        'CLASS': 'DummyInterface',
    },
    'IFCONFIG': {
        'LABEL': 'Dummy1',
        'ADDRESS': 'DummyAddress',
        'SerialNumber': '1234',
    }
}

dummycpc_inst_cfg = {
    'INSTRUMENT': {
        'MODULE': 'daq.instrument.instrument',
        'CLASS': 'DummyInstrument',
    },
    'INSTCONFIG': {
        'DESCRIPTION': {
            'LABEL': 'DummyCPC',
            'SERIAL_NUMBER': '0001',
            'PROPERTY_NUMBER': 'CD0000001',
        },
        'IFACE_LIST': {
            'DUMMY1': {
                'IFACE_CONFIG': dummy1_iface_cfg,
                'OPERATION': {
                    'POLLED': False,
                    'SAMPLE_FREQ_SEC': 1,
                },
            },
        },
    },
    # could be IFACE_LIST to allow for multiple iface
}

dummy_controller_cfg = {
    'CONTROLLER': {
        'MODULE': 'daq.controller.controller',
        'CLASS': 'Controller',
    }
}
