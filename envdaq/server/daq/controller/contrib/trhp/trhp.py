from daq.instrument.instrument import Instrument
from daq.controller.controller import Controller
from data.message import Message


class TRHPController(Controller):
    INSTANTIABLE = True
    # def __init__(self, config):

    def __init__(self, config, **kwargs):
        super(TRHPController, self).__init__(config, **kwargs)
        self.name = 'TRHPController'

        # self.INSTANTIABLE = True

        # DummyController.set_instantiable(True)
        # DummyController.INSTANTIABLE = True
        # DAQ.INSTANTIABLE = True
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

    def configure_components(self):

        self.component_map['INSTRUMENTS'] = {
            'trhp': {
                'LIST': [],
                'PRIMARY': None
            }
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

        if len(self.component_map['INSTRUMENTS']['trhp']['LIST']) > 0:
            # configure GPS measurements
            # TODO: how to specify primary GPS (or other) meas?
            trhp = dict()

            # size_dist_y_data = []
            # size_dist_default_y_data = []

            for inst in self.component_map['INSTRUMENTS']['trhp']['LIST']:

                ts1d_y_data = []
                ts1d_default_y_data = []
                ts1d_meas = {
                    'primary': dict(),
                }

                inst_meta = inst.get_metadata()
                inst_alias = inst_meta['alias']
                inst_id = inst_meta['ID']

                inst_meas = inst_meta['measurement_meta']
                inst_plots = inst_meta['plot_meta']

                # meas_meta[inst_id] = dict()
                # meas_meta[inst_id]['alias'] = inst_alias
                trhp[inst_id] = dict()
                trhp[inst_id]['alias'] = inst_alias
                trhp[inst_id]['measurement_meta'] = dict()
                trhp[inst_id]['measurement_meta']['primary'] = dict()
                mm = trhp[inst_id]['measurement_meta']['primary']
                for mtype, meas in inst_meas.items():
                    if 'temperature' in meas:
                        mm['temperature'] = (
                            meas['temperature']
                        )
                        # meas_meta[inst_id]['latitude'] = {
                        # trhp[inst_id]['latitude'] = {
                        #     'measurement_meta': meas['latitude'],
                        # }
                        ts1d_y_data.append('temperature')
                        ts1d_meas['primary']['temperature'] = (
                            meas['temperature']
                        )

                    if 'relative_humidity' in meas:
                        mm['relative_humidity'] = (
                            meas['relative_humidity']
                        )
                        # meas_meta[inst_id]['longitude'] = {
                        # trhp[inst_id]['longitude'] = {
                        #     'measurement_meta': meas['longitude'],
                        # }
                        ts1d_y_data.append('relative_humidity')
                        ts1d_meas['primary']['relative_humidity'] = meas['relative_humidity']

                    if 'pressure' in meas:
                        mm['pressure'] = (
                            meas['pressure']
                        )
                        # meas_meta[inst_id]['altitude'] = {
                        # trhp[inst_id]['altitude'] = {
                        #     'measurement_meta': meas['altitude'],
                        # }
                        ts1d_y_data.append('pressure')
                        # ts1d_default_y_data.append('pressure')
                        ts1d_meas['primary']['pressure'] = meas['pressure']

                ts1d_source_map[inst_id] = {
                    'y_data': {
                        'default': ts1d_y_data
                    },
                    'default_y_data': ts1d_default_y_data,
                    'alias': inst_alias,
                    'measurement_meta': ts1d_meas
                }

            meas_meta['trhp'] = trhp

        # add controller measurements
        # if (
        #     len(self.component_map['INSTRUMENTS']['GPS']['LIST']) > 0 and
        #     len(self.component_map['INSTRUMENTS']['DUMMY']['LIST']) > 0
        # ):
        #     # configure GPS measurements
        #     ctr_meas = dict()
        #     ctr_meas[self.get_id()] = dict()
        #     ctr_meas[self.get_id()]['alias'] = self.alias
        #     ctr_meas[self.get_id()]['measurement_meta'] = dict()

        #     ts1d_y_data = []
        #     ts1d_default_y_data = []
        #     ts1d_meas = {
        #         # 'primary': dict(),
        #     }

        #     sd_y_data = []
        #     sd_default_y_data = []
        #     sd_meas = {
        #         # 'primary': dict(),
        #     }

        #     geo_z_data = []
        #     geo_meas = {
        #         # 'primary': dict(),
        #     }

        #     # y_data = []
        #     # dist_data = []

        #     primary_meas_2d = dict()
        #     primary_meas_2d['dndlogdp'] = {
        #         'dimensions': {
        #             'axes': ['TIME', 'DIAMETER'],
        #             'unlimited': 'TIME',
        #             'units': ['dateTime', 'um'],
        #         },
        #         'units': 'cm-3',  # should be cfunits or udunits
        #         'uncertainty': 0.1,
        #         'source': 'CALCULATED',
        #         'data_type': 'NUMERIC',
        #         # 'short_name': 'bin_conc',
        #         # 'parse_label': 'bin',
        #         'control': None,
        #         'axes': {
        #             # 'TIME', 'datetime',
        #             'DIAMETER': 'inverted_diameter_um',
        #         }
        #     }
        #     sd_y_data.append('dndlogdp')

        #     primary_meas_2d['inverted_diameter_um'] = {
        #         'dimensions': {
        #             'axes': ['TIME', 'DIAMETER'],
        #             'unlimited': 'TIME',
        #             'units': ['dateTime', 'um'],
        #         },
        #         'units': 'um',  # should be cfunits or udunits
        #         'uncertainty': 0.1,
        #         'source': 'CALCULATED',
        #         'data_type': 'NUMERIC',
        #         'short_name': 'inverted_dp',
        #         # 'parse_label': 'diameter',
        #         'control': None,
        #         'axes': {
        #             # 'TIME', 'datetime',
        #             'DIAMETER': 'inverted_diameter_um',
        #         }
        #     }
        #     sd_y_data.append('inverted_diameter_um')

        #     primary_meas = dict()
        #     primary_meas['integral_concentration'] = {
        #         'dimensions': {
        #             'axes': ['TIME'],
        #             'unlimited': 'TIME',
        #             'units': ['dateTime'],
        #         },
        #         'units': 'cm-3',  # should be cfunits or udunits
        #         'uncertainty': 0.2,
        #         'source': 'calculated',
        #         'data_type': 'NUMERIC',
        #         'short_name': 'int_conc',
        #         # 'parse_label': 'scan_max_volts',
        #         'control': None,
        #     }
        #     ts1d_y_data.append('integral_concentration')
        #     geo_z_data.append('integral_concentration')

        #     ctr_meas[self.get_id()]['measurement_meta']['primary_2d'] = (
        #         primary_meas_2d
        #     )
        #     ctr_meas[self.get_id()]['measurement_meta']['primary'] = (
        #         primary_meas
        #     )

        #     ts1d_meas['primary'] = primary_meas
        #     ts1d_source_map[self.get_id()] = {
        #         'y_data': {
        #             'default': ts1d_y_data
        #         },
        #         'default_y_data': ts1d_default_y_data,
        #         'alias': self.alias,
        #         'measurement_meta': ts1d_meas
        #     }

        #     sd_meas['primary_2d'] = primary_meas_2d
        #     sd_source_map[self.get_id()] = {
        #         'y_data': {
        #             'default': sd_y_data
        #         },
        #         'default_y_data': sd_default_y_data,
        #         'alias': self.alias,
        #         'measurement_meta': sd_meas
        #     }

        #     geo_meas['primary'] = primary_meas
        #     geo_source_map[self.get_id()] = {
        #         'z_data': {
        #             'default': geo_z_data
        #         },
        #         'default_z_data': [],
        #         'alias': self.alias,
        #         'measurement_meta': geo_meas,
        #         'instrument_type': 'DUMMY'
        #     }

        #     meas_meta['CONTROLLER'] = ctr_meas

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

        self.plot_config['app_list'] = self.plot_list

        self.measurements['meta'] = meas_meta

        # build plot_meta

    async def handle(self, msg, type=None):
        # print(f'%%%%%Instrument.handle: {msg.to_json()}')
        # handle messages from multiple sources. What ID to use?
        if (type == 'FromChild' and msg.type == Instrument.class_type):
            # id = msg.sender_id
            # entry = self.parse(msg)
            # self.last_entry = entry
            # print('entry = \n{}'.format(entry))
            pass
            # entry = self.calculate_data(msg)
            # entry = None
            # if entry:
            #     data = Message(
            #         sender_id=self.get_id(),
            #         msgtype=Controller.class_type,
            #     )
            #     # send data to next step(s)
            #     # to controller
            #     # data.update(subject='DATA', body=entry['DATA'])
            #     data.update(subject='DATA', body=entry)
            #     # print(f'instrument data: {data.to_json()}')

            #     await self.message_to_ui(data)
            #     if self.datafile:
            #         await self.datafile.write_message(data)
                # await asyncio.sleep(.1)
                # await PlotManager.update_data(self.plot_name, data.to_json())

            # print(f'data_json: {data.to_json()}\n')
        elif type == 'FromUI':
            if (
                msg.subject == 'STATUS' and
                msg.body['purpose'] == 'REQUEST'
            ):
                print(f'msg: {msg.body}')
                self.send_status()

            elif (
                msg.subject == 'CONTROLS' and
                msg.body['purpose'] == 'REQUEST'
            ):
                print(f'msg: {msg.body}')
                await self.set_control(msg.body['control'], msg.body['value'])

            elif (
                msg.subject == 'RUNCONTROLS' and
                msg.body['purpose'] == 'REQUEST'
            ):
                print(f'msg: {msg.body}')
                await self.handle_control_action(
                    msg.body['control'], msg.body['value']
                )

    # def calculate_data(self, msg):

    #     id = msg.sender_id
    #     if len(self.component_map['INSTRUMENTS']['DUMMY']['LIST']) > 0:
    #         dummy = self.component_map['INSTRUMENTS']['DUMMY']['LIST'][0]
    #         if id == dummy.get_id():
    #             dt = msg.body['DATA']['DATETIME']
    #             measurements = msg.body['DATA']['MEASUREMENTS']
    #             dp = measurements['diameter']['VALUE']
    #             dlogdp = math.pow(
    #                 10,
    #                 math.log10(dp[1]/dp[0])
    #             )

    #             size_dist = measurements['size_distribution']['VALUE']
    #             dndlogdp = []
    #             intN = 0
    #             for bin in size_dist:
    #                 dndlogdp.append(round(bin/dlogdp, 3))
    #                 intN += bin

    #             entry = {
    #                 'DATA': {
    #                     'DATETIME': dt,
    #                     'MEASUREMENTS': {
    #                         'dndlogdp': {
    #                             'VALUE': dndlogdp
    #                         },
    #                         'inverted_diameter_um': {
    #                             'VALUE': dp,
    #                         },
    #                         'integral_concentration': {
    #                             'VALUE': round(intN, 3)
    #                         }
    #                     }
    #                 }

    #             }

    #             if len(self.alias) > 0:
    #                 entry['alias'] = self.alias

    #             return entry
    #     return None

    async def handle_control_action(self, control, value):
        pass
        if control and value:
            if control == 'start_stop':
                if value == 'START':
                    self.start()
                elif value == 'STOP':
                    self.stop()

    def get_definition_instance(self):
        return TRHPController.get_definition()

    def get_definition():
        definition = dict()
        definition['module'] = TRHPController.__module__
        definition['name'] = TRHPController.__name__
        definition['tags'] = [
            'temperature',
            'rh',
            'pressure',
            'environmental',
        ]

        return {'DEFINITION': definition}
