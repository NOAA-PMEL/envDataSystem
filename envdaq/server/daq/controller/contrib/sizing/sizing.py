import asyncio
from daq.daq import DAQ
from daq.instrument.instrument import InstrumentFactory, Instrument
from data.message import Message
from daq.controller.controller import Controller, ControllerFactory

class SizingSystem(Controller):
    INSTANTIABLE = True
    # def __init__(self, config):

    def __init__(self, config, **kwargs):
        super(SizingSystem, self).__init__(config, **kwargs)
        self.name = 'SizingSystem'

        self.aitken_dmps = None
        self.accum_dmps = None
        self.aps = None

        self.setup()

    def setup(self):
        super().setup()
        # add extra here

        # build dummy istrument map
        # self.dummy_instrument_map = dict()
        # for inst_id, inst in self.instrument_map.items():
        #     print(f'()()() setup: {inst.type}, {inst.label}, {inst.alias}')
        #     if 'dummy' in inst.tag_list:
        #         self.dummy_instrument_map[inst_id] = {
        #             'instrument': inst,
        #             # anything else? alias? label?
        #         }

        # print(f'dummy_map: {self.dummy_instrument_map}')

                #     dlogdp = math.pow(
                #         10,
                #         math.log10(max_dp/min_dp)/(30-1)
                #     )


    def configure_components(self):

        self.component_map['INSTRUMENTS'] = {
            'aitken_dmps': {
                'LIST': [],
                'PRIMARY': None
            },
            'accum_dmps': {
                'LIST': [],
                'PRIMARY': None
            },
            'aps': {
                'LIST': [],
                'PRIMARY': None
            },
        }

    def build_controller_meta(self):

        meas_meta = dict()
        self.plot_config = {
            'plots': dict(),
        }

        time_series1d = {
            'app_type': 'TimeSeries1D',
            'source_map': dict(),
        }
        ts1d_source_map = dict()

        size_dist = {
            'app_type': 'SizeDistribution',
            'source_map': dict(),
        }
        sd_source_map = dict()


        if len(self.component_map['INSTRUMENTS']['aitken_dmps']['LIST']) > 0:
            # configure GPS measurements
            # TODO: how to specify primary GPS (or other) meas?
            aitken = dict()

            # size_dist_y_data = []
            # size_dist_default_y_data = []

            for inst in self.component_map['INSTRUMENTS']['aitken_dmps']['LIST']:

                ts1d_y_data = []
                ts1d_default_y_data = []
                ts1d_meas = {
                    'primary': dict(),
                }

                sd_y_data = []
                sd_default_y_data = []
                sd_meas = {
                    'primary': dict(),
                }

                # geo_z_data = []
                # geo_meas = {
                #     'primary': dict(),
                # }

                inst_meta = inst.get_metadata()
                inst_alias = inst_meta['alias']
                inst_id = inst_meta['ID']

                inst_meas = inst_meta['measurement_meta']
                inst_plots = inst_meta['plot_meta']

                # meas_meta[inst_id] = dict()
                # meas_meta[inst_id]['alias'] = inst_alias
                aitken[inst_id] = dict()
                aitken[inst_id]['alias'] = inst_alias
                aitken[inst_id]['measurement_meta'] = dict()
                aitken[inst_id]['measurement_meta']['primary'] = dict()
                mm = aitken[inst_id]['measurement_meta']['primary']
                for mtype, meas in inst_meas.items():
                    if 'integral_concentration' in meas:
                        mm['integral_concentration'] = (
                            meas['integral_concentration']
                        )
                        # meas_meta[inst_id]['latitude'] = {
                        # gps[inst_id]['latitude'] = {
                        #     'measurement_meta': meas['latitude'],
                        # }
                        ts1d_y_data.append('integral_concentration')
                        ts1d_meas['primary']['integral_concentration'] = (
                            meas['integral_concentration']
                        )

                        # geo_z_data.append('latitude')
                        # geo_lat_dim = 'latitude'
                        # geo_meas['primary']['latitude'] = meas['latitude']

                    if 'bin_concentration' in meas:
                        mm['bin_concentration'] = (
                            meas['bin_concentration']
                        )
                        # {
                        # # dummy[inst_id]['size_distribution'] = {
                        #     'measurement_meta': meas['size_distribution'],
                        # }
                        sd_y_data.append('bin_concentration')
                        sd_meas['primary']['bin_concentration'] = (
                            meas['bin_concentration']
                        )
                    if 'diameter_um' in meas:
                        mm['diameter_um'] = (
                            meas['diameter_um']
                        )
                        # meas_meta[inst_id]['diameter'] = {
                        # dummy[inst_id]['diameter'] = {
                        #     'measurement_meta': meas['diameter'],
                        # }
                        sd_y_data.append('diameter_um')
                        sd_meas['primary']['diameter_um'] = (
                            meas['diameter_um']
                        )

                ts1d_source_map[inst_id] = {
                    'y_data': ts1d_y_data,
                    'default_y_data': ts1d_default_y_data,
                    'alias': inst_alias,
                    'measurement_meta': ts1d_meas
                }

                sd_source_map[inst_id] = {
                    'y_data': sd_y_data,
                    'default_y_data': sd_default_y_data,
                    'alias': inst_alias,
                    'measurement_meta': sd_meas
                }

                # main_gps = self.component_map['INSTRUMENTS']['GPS']['PRIMARY']
                # geo_source_map[inst_id] = {
                #     'z_data': geo_z_data,
                #     'default_z_data': [],
                #     'alias': inst_alias,
                #     'measurement_meta': geo_meas,
                #     'latitude': geo_lat_dim,
                #     'longitude': geo_lon_dim,
                #     'altitude': geo_alt_dim,
                #     'primary_gps': main_gps,
                #     'instrument_type': 'GPS'
                # }

            meas_meta['aitken_dmps'] = aitken

        if len(self.component_map['INSTRUMENTS']['accum_dmps']['LIST']) > 0:
            # configure GPS measurements
            # TODO: how to specify primary GPS (or other) meas?
            accum = dict()

            # size_dist_y_data = []
            # size_dist_default_y_data = []

            for inst in self.component_map['INSTRUMENTS']['accum_dmps']['LIST']:

                ts1d_y_data = []
                ts1d_default_y_data = []
                ts1d_meas = {
                    'primary': dict(),
                }

                sd_y_data = []
                sd_default_y_data = []
                sd_meas = {
                    'primary': dict(),
                }

                # geo_z_data = []
                # geo_meas = {
                #     'primary': dict(),
                # }

                inst_meta = inst.get_metadata()
                inst_alias = inst_meta['alias']
                inst_id = inst_meta['ID']

                inst_meas = inst_meta['measurement_meta']
                inst_plots = inst_meta['plot_meta']

                # meas_meta[inst_id] = dict()
                # meas_meta[inst_id]['alias'] = inst_alias
                accum[inst_id] = dict()
                accum[inst_id]['alias'] = inst_alias
                accum[inst_id]['measurement_meta'] = dict()
                accum[inst_id]['measurement_meta']['primary'] = dict()
                mm = accum[inst_id]['measurement_meta']['primary']
                for mtype, meas in inst_meas.items():
                    if 'integral_concentration' in meas:
                        mm['integral_concentration'] = (
                            meas['integral_concentration']
                        )
                        # meas_meta[inst_id]['latitude'] = {
                        # gps[inst_id]['latitude'] = {
                        #     'measurement_meta': meas['latitude'],
                        # }
                        ts1d_y_data.append('integral_concentration')
                        ts1d_meas['primary']['integral_concentration'] = (
                            meas['integral_concentration']
                        )

                        # geo_z_data.append('latitude')
                        # geo_lat_dim = 'latitude'
                        # geo_meas['primary']['latitude'] = meas['latitude']

                    if 'bin_concentration' in meas:
                        mm['bin_concentration'] = (
                            meas['bin_concentration']
                        )
                        # {
                        # # dummy[inst_id]['size_distribution'] = {
                        #     'measurement_meta': meas['size_distribution'],
                        # }
                        sd_y_data.append('bin_concentration')
                        sd_meas['primary']['bin_concentration'] = (
                            meas['bin_concentration']
                        )
                    if 'diameter_um' in meas:
                        mm['diameter_um'] = (
                            meas['diameter_um']
                        )
                        # meas_meta[inst_id]['diameter'] = {
                        # dummy[inst_id]['diameter'] = {
                        #     'measurement_meta': meas['diameter'],
                        # }
                        sd_y_data.append('diameter_um')
                        sd_meas['primary']['diameter_um'] = (
                            meas['diameter_um']
                        )

                ts1d_source_map[inst_id] = {
                    'y_data': ts1d_y_data,
                    'default_y_data': ts1d_default_y_data,
                    'alias': inst_alias,
                    'measurement_meta': ts1d_meas
                }

                sd_source_map[inst_id] = {
                    'y_data': sd_y_data,
                    'default_y_data': sd_default_y_data,
                    'alias': inst_alias,
                    'measurement_meta': sd_meas
                }

                # main_gps = self.component_map['INSTRUMENTS']['GPS']['PRIMARY']
                # geo_source_map[inst_id] = {
                #     'z_data': geo_z_data,
                #     'default_z_data': [],
                #     'alias': inst_alias,
                #     'measurement_meta': geo_meas,
                #     'latitude': geo_lat_dim,
                #     'longitude': geo_lon_dim,
                #     'altitude': geo_alt_dim,
                #     'primary_gps': main_gps,
                #     'instrument_type': 'GPS'
                # }

            meas_meta['accum_dmps'] = accum

        if len(self.component_map['INSTRUMENTS']['aps']['LIST']) > 0:
            # configure GPS measurements
            # TODO: how to specify primary GPS (or other) meas?
            aps = dict()

            # size_dist_y_data = []
            # size_dist_default_y_data = []

            for inst in self.component_map['INSTRUMENTS']['aps']['LIST']:

                ts1d_y_data = []
                ts1d_default_y_data = []
                ts1d_meas = {
                    'primary': dict(),
                }

                sd_y_data = []
                sd_default_y_data = []
                sd_meas = {
                    'primary': dict(),
                }

                # geo_z_data = []
                # geo_meas = {
                #     'primary': dict(),
                # }

                inst_meta = inst.get_metadata()
                inst_alias = inst_meta['alias']
                inst_id = inst_meta['ID']

                inst_meas = inst_meta['measurement_meta']
                inst_plots = inst_meta['plot_meta']

                # meas_meta[inst_id] = dict()
                # meas_meta[inst_id]['alias'] = inst_alias
                aps[inst_id] = dict()
                aps[inst_id]['alias'] = inst_alias
                aps[inst_id]['measurement_meta'] = dict()
                aps[inst_id]['measurement_meta']['primary'] = dict()
                mm = aps[inst_id]['measurement_meta']['primary']
                for mtype, meas in inst_meas.items():
                    if 'integral_concentration' in meas:
                        mm['integral_concentration'] = (
                            meas['integral_concentration']
                        )
                        # meas_meta[inst_id]['latitude'] = {
                        # gps[inst_id]['latitude'] = {
                        #     'measurement_meta': meas['latitude'],
                        # }
                        ts1d_y_data.append('integral_concentration')
                        ts1d_meas['primary']['integral_concentration'] = (
                            meas['integral_concentration']
                        )

                        # geo_z_data.append('latitude')
                        # geo_lat_dim = 'latitude'
                        # geo_meas['primary']['latitude'] = meas['latitude']

                    if 'bin_concentration' in meas:
                        mm['bin_concentration'] = (
                            meas['bin_concentration']
                        )
                        # {
                        # # dummy[inst_id]['size_distribution'] = {
                        #     'measurement_meta': meas['size_distribution'],
                        # }
                        sd_y_data.append('bin_concentration')
                        sd_meas['primary']['bin_concentration'] = (
                            meas['bin_concentration']
                        )
                    if 'diameter_um' in meas:
                        mm['diameter_um'] = (
                            meas['diameter_um']
                        )
                        # meas_meta[inst_id]['diameter'] = {
                        # dummy[inst_id]['diameter'] = {
                        #     'measurement_meta': meas['diameter'],
                        # }
                        sd_y_data.append('diameter_um')
                        sd_meas['primary']['diameter_um'] = (
                            meas['diameter_um']
                        )

                ts1d_source_map[inst_id] = {
                    'y_data': ts1d_y_data,
                    'default_y_data': ts1d_default_y_data,
                    'alias': inst_alias,
                    'measurement_meta': ts1d_meas
                }

                sd_source_map[inst_id] = {
                    'y_data': sd_y_data,
                    'default_y_data': sd_default_y_data,
                    'alias': inst_alias,
                    'measurement_meta': sd_meas
                }

                # main_gps = self.component_map['INSTRUMENTS']['GPS']['PRIMARY']
                # geo_source_map[inst_id] = {
                #     'z_data': geo_z_data,
                #     'default_z_data': [],
                #     'alias': inst_alias,
                #     'measurement_meta': geo_meas,
                #     'latitude': geo_lat_dim,
                #     'longitude': geo_lon_dim,
                #     'altitude': geo_alt_dim,
                #     'primary_gps': main_gps,
                #     'instrument_type': 'GPS'
                # }

            meas_meta['aps'] = aps

        # controller derived measurements
        # TODO: define these in get_definition like instrument
        #       and retrieve with add_measurements to populate
        #       self.measurements
        sizing = dict()

        # size_dist_y_data = []
        # size_dist_default_y_data = []

        # for inst in self.component_map['INSTRUMENTS']['sizing']['LIST']:

        ts1d_y_data = []
        ts1d_default_y_data = []
        ts1d_meas = {
            'primary': dict(),
        }

        sd_y_data = []
        sd_default_y_data = []
        sd_meas = {
            'primary': dict(),
        }

            # geo_z_data = []
            # geo_meas = {
            #     'primary': dict(),
            # }
        # cont_meta
        #     inst_meta = inst.get_metadata()
        #     inst_alias = inst_meta['alias']
        #     inst_id = inst_meta['ID']

        #     inst_meas = inst_meta['measurement_meta']
        #     inst_plots = inst_meta['plot_meta']

        #     # meas_meta[inst_id] = dict()
        #     # meas_meta[inst_id]['alias'] = inst_alias
        #     sizing[inst_id] = dict()
        #     sizing[inst_id]['alias'] = inst_alias
        #     sizing[inst_id]['measurement_meta'] = dict()
        #     sizing[inst_id]['measurement_meta']['primary'] = dict()
        #     mm = sizing[inst_id]['measurement_meta']['primary']
        #     for mtype, meas in inst_meas.items():
        #         if 'integral_concentration' in meas:
        #             mm['integral_concentration'] = (
        #                 meas['integral_concentration']
        #             )
        #             # meas_meta[inst_id]['latitude'] = {
        #             # gps[inst_id]['latitude'] = {
        #             #     'measurement_meta': meas['latitude'],
        #             # }
        #             ts1d_y_data.append('integral_concentration')
        #             ts1d_meas['primary']['integral_concentration'] = (
        #                 meas['integral_concentration']
        #             )

        #             # geo_z_data.append('latitude')
        #             # geo_lat_dim = 'latitude'
        #             # geo_meas['primary']['latitude'] = meas['latitude']

        #         if 'bin_concentration' in meas:
        #             mm['bin_concentration'] = (
        #                 meas['bin_concentration']
        #             )
        #             # {
        #             # # dummy[inst_id]['size_distribution'] = {
        #             #     'measurement_meta': meas['size_distribution'],
        #             # }
        #             sd_y_data.append('bin_concentration')
        #             sd_meas['primary']['bin_concentration'] = (
        #                 meas['bin_concentration']
        #             )
        #         if 'diameter_um' in meas:
        #             mm['diameter_um'] = (
        #                 meas['diameter_um']
        #             )
        #             # meas_meta[inst_id]['diameter'] = {
        #             # dummy[inst_id]['diameter'] = {
        #             #     'measurement_meta': meas['diameter'],
        #             # }
        #             sd_y_data.append('diameter_um')
        #             sd_meas['primary']['diameter_um'] = (
        #                 meas['diameter_um']
        #             )

        #     ts1d_source_map[inst_id] = {
        #         'y_data': ts1d_y_data,
        #         'default_y_data': ts1d_default_y_data,
        #         'alias': inst_alias,
        #         'measurement_meta': ts1d_meas
        #     }

        #     sd_source_map[inst_id] = {
        #         'y_data': sd_y_data,
        #         'default_y_data': sd_default_y_data,
        #         'alias': inst_alias,
        #         'measurement_meta': sd_meas
        #     }

            # main_gps = self.component_map['INSTRUMENTS']['GPS']['PRIMARY']
            # geo_source_map[inst_id] = {
            #     'z_data': geo_z_data,
            #     'default_z_data': [],
            #     'alias': inst_alias,
            #     'measurement_meta': geo_meas,
            #     'latitude': geo_lat_dim,
            #     'longitude': geo_lon_dim,
            #     'altitude': geo_alt_dim,
            #     'primary_gps': main_gps,
            #     'instrument_type': 'GPS'
            # }

        meas_meta['sizing'] = sizing

        # add controller measurements
        # print('here')
        # add controls

        prefix = self.alias['prefix']
        self.plot_list = []

        # Add TimeSeries
        time_series1d['source_map'] = ts1d_source_map
        plot_name = prefix + '_ts1d'
        self.plot_config['plots'][plot_name] = time_series1d
        app_name = '/controller_' + self.alias['name'] + '_' + plot_name
        self.plot_config['plots'][plot_name]['app_name'] = app_name
        self.plot_list.append(app_name)

        # Add SizeDist
        size_dist['source_map'] = sd_source_map
        plot_name = prefix + '_raw_size_dist'
        self.plot_config['plots'][plot_name] = size_dist
        app_name = '/controller_' + self.alias['name'] + '_' + plot_name
        self.plot_config['plots'][plot_name]['app_name'] = app_name
        self.plot_list.append(app_name)

        # Add GeoMapPlot
        geo_plot['source_map'] = geo_source_map
        plot_name = prefix + '_geo_map'
        self.plot_config['plots'][plot_name] = geo_plot
        app_name = '/controller_' + self.alias['name'] + '_' + plot_name
        self.plot_config['plots'][plot_name]['app_name'] = app_name
        self.plot_list.append(app_name)

        self.plot_config['app_list'] = self.plot_list

        self.measurements['meta'] = meas_meta

        # build plot_meta

    async def handle(self, msg, type=None):
        # print(f'%%%%%Instrument.handle: {msg.to_json()}')
        # handle messages from multiple sources. What ID to use?
        if (type == 'FromChild' and msg.type == Instrument.class_type):
            id = msg.sender_id
            # entry = self.parse(msg)
            # self.last_entry = entry
            # print('entry = \n{}'.format(entry))

            data = Message(
                sender_id=self.get_id(),
                msgtype=Controller.class_type,
            )
            # send data to next step(s)
            # to controller
            # data.update(subject='DATA', body=entry['DATA'])
            data.update(subject='DATA', body=entry)
            # print(f'instrument data: {data.to_json()}')

            await self.message_to_ui(data)
            # await PlotManager.update_data(self.plot_name, data.to_json())

            # print(f'data_json: {data.to_json()}\n')
        elif type == 'FromUI':
            if msg.subject == 'STATUS' and msg.body['purpose'] == 'REQUEST':
                print(f'msg: {msg.body}')
                self.send_status()

            elif msg.subject == 'CONTROLS' and msg.body['purpose'] == 'REQUEST':
                print(f'msg: {msg.body}')
                await self.set_control(msg.body['control'], msg.body['value'])
            elif msg.subject == 'RUNCONTROLS' and msg.body['purpose'] == 'REQUEST':
                print(f'msg: {msg.body}')
                await self.handle_control_action(msg.body['control'], msg.body['value'])
                # await self.set_control(msg.body['control'], msg.body['value'])

        # print("DummyInstrument:msg: {}".format(msg.body))
        # else:
        #     await asyncio.sleep(0.01)

    async def handle_control_action(self, control, value):
        pass
        if control and value:
            if control == 'start_stop':
                if value == 'START':
                    self.start()
                elif value == 'STOP':
                    self.stop()

        #     elif control == 'inlet_temperature_sp':
        #         # check bounds
        #         # send command to instrument via interface
        #         cmd = Message(
        #             sender_id=self.get_id(),
        #             msgtype=Instrument.class_type,
        #             subject="COMMAND",
        #             body='inlet_temp='+value,
        #         )

        #         # print(f'{self.iface_map}')
        #         # await self.to_child_buf.put(cmd)
        #         await self.iface_map['DummyInterface:test_interface'].message_from_parent(cmd)
        #         self.set_control_att(control, 'action_state', 'OK')

    # def _create_definition(self):
    #     self.daq_definition['module'] = self.__module__
    #     self.daq_definition['class'] = self.__name__

    def get_definition_instance(self):
        return SizingSystem.get_definition()

    def get_definition():
        definition = dict()
        definition['module'] = SizingSystem.__module__
        definition['name'] = SizingSystem.__name__
        definition['tags'] = [
            'size distribution',
            'particle',
            'aerosol',
            'physics',
            'aitken mode',
            'accumulation mode',
            'coarse mode',
            'sizing',
            'inverted'        
        ]

        measurement_config = dict()

        y_data = []
        dist_data = []

        primary_meas_2d = dict()
        primary_meas_2d['dmps_dndlogdp'] = {
            'dimensions': {
                'axes': ['TIME', 'DIAMETER'],
                'unlimited': 'TIME',
                'units': ['dateTime', 'um'],
            },
            'units': 'cm-3',  # should be cfunits or udunits
            'uncertainty': 0.1,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            # 'short_name': 'bin_conc',
            # 'parse_label': 'bin',
            'control': None,
            'axes': {
                # 'TIME', 'datetime',
                'DIAMETER': 'dmps_diameter_um',
            }
        }
        dist_data.append('dmps_dndlogdp')

        primary_meas_2d['dmps_diameter_um'] = {
            'dimensions': {
                'axes': ['TIME', 'DIAMETER'],
                'unlimited': 'TIME',
                'units': ['dateTime', 'um'],
            },
            'units': 'um',  # should be cfunits or udunits
            'uncertainty': 0.1,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            'short_name': 'dmps_dp',
            # 'parse_label': 'diameter',
            'control': None,
        }
        dist_data.append('dmps_diameter_um')

        primary_meas_2d = dict()
        primary_meas_2d['aps_dndlogdp'] = {
            'dimensions': {
                'axes': ['TIME', 'DIAMETER'],
                'unlimited': 'TIME',
                'units': ['dateTime', 'um'],
            },
            'units': 'cm-3',  # should be cfunits or udunits
            'uncertainty': 0.1,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            # 'short_name': 'bin_conc',
            # 'parse_label': 'bin',
            'control': None,
            'axes': {
                # 'TIME', 'datetime',
                'DIAMETER': 'aps_diameter_aero_um',
            }
        }
        dist_data.append('aps_dndlogdp')

        primary_meas_2d['aps_diameter_aero_um'] = {
            'dimensions': {
                'axes': ['TIME', 'DIAMETER'],
                'unlimited': 'TIME',
                'units': ['dateTime', 'um'],
            },
            'units': 'um',  # should be cfunits or udunits
            'uncertainty': 0.1,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            'short_name': 'aps_dpa',
            # 'parse_label': 'diameter',
            'control': None,
        }
        dist_data.append('aps_diameter_aero_um')

        primary_meas = dict()
        primary_meas['integral_concentration'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'cm-3',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'calculated',
            'data_type': 'NUMERIC',
            'short_name': 'int_conc',
            # 'parse_label': 'scan_max_volts',
            'control': None,
        }
        y_data.append('integral_concentration')

        measurement_config['primary_2d'] = primary_meas_2d
        measurement_config['primary'] = primary_meas
        definition['measurement_config'] = measurement_config

        plot_config = dict()

        size_dist = dict()
        size_dist['app_type'] = 'SizeDistribution'
        size_dist['y_data'] = dist_data,
        size_dist['default_y_data'] = [
            'dmps_dndlogdp',
            'aps_dndlogdp'
        ]
        source_map = {
            'default': {
                'y_data': dist_data,
                'default_y_data': [
                    'dmps_dndlogdp',
                    'aps_dndlogdp'
                ]
            },
        }
        size_dist['source_map'] = source_map

        time_series1d = dict()
        time_series1d['app_type'] = 'TimeSeries1D'
        time_series1d['y_data'] = y_data
        time_series1d['default_y_data'] = ['integral_concentration']
        source_map = {
            'default': {
                'y_data': y_data,
                'default_y_data': ['integral_concentration']
            },
        }
        time_series1d['source_map'] = source_map

        plot_config['plots'] = dict()
        plot_config['plots']['inverted_size_dist'] = size_dist
        plot_config['plots']['main_ts1d'] = time_series1d
        definition['plot_config'] = plot_config

        return {'DEFINITION': definition}
        # DAQ.daq_definition['DEFINITION'] = definition
        # return DAQ.daq_definition
