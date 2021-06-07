# import asyncio
# from daq.daq import DAQ
from daq.instrument.instrument import InstrumentFactory, Instrument
# from data.message import Message
from daq.controller.controller import Controller, ControllerFactory
# import math
# import subprocess
# from datetime import datetime


class SimpleTSController(Controller):
    INSTANTIABLE = True
    # def __init__(self, config):

    def __init__(self, config, **kwargs):
        super(SimpleTSController, self).__init__(config, **kwargs)
        self.name = 'SimpleTSController'

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

    async def shutdown(self):
        self.stop()
        self.disable()
        await self.deregister_from_UI()

        # TODO need to wait for deregister before closing loops and connection
        await super().shutdown()


    def configure_components(self):

        self.component_map['INSTRUMENTS'] = {
            'default': {
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

        if len(self.component_map['INSTRUMENTS']['default']['LIST']) > 0:
            # configure GPS measurements
            # TODO: how to specify primary GPS (or other) meas?
            default = dict()

            self.has_default = True

            # size_dist_y_data = []
            # size_dist_default_y_data = []

            for inst in self.component_map['INSTRUMENTS']['default']['LIST']:

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
                default[inst_id] = dict()
                default[inst_id]['alias'] = inst_alias
                default[inst_id]['measurement_meta'] = dict()
                default[inst_id]['measurement_meta']['primary'] = dict()
                mm = default[inst_id]['measurement_meta']['primary']

                if "primary" in inst_meas:
                    for name, meas in inst_meas["primary"].items():
                        mm[name] = meas
                        ts1d_y_data.append(name)
                        ts1d_meas['primary'][name] = meas



                ts1d_source_map[inst_id] = {
                    'y_data': {
                        'default': ts1d_y_data
                    },
                    'default_y_data': ts1d_default_y_data,
                    'alias': inst_alias,
                    'measurement_meta': ts1d_meas
                }

            meas_meta['default'] = default


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

            # entry = self.calculate_data(msg)
            pass

            # TODO: save data if needed
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
            # if self.datafile:
            #     await self.datafile.write_message(data)

            # print(f'data_json: {data.to_json()}\n')
        elif type == 'FromUI':
            if msg.subject == 'STATUS' and msg.body['purpose'] == 'REQUEST':
                # print(f'msg: {msg.body}')
                self.send_status()

            elif (
                msg.subject == 'CONTROLS' and
                msg.body['purpose'] == 'REQUEST'
            ):
                # print(f'msg: {msg.body}')
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

    #     # TODO: add get_data entry functions to controller

    #     id = msg.sender_id
    #     dt = msg.body['DATA']['DATETIME']

    #     if self.has_aitken and self.has_accum:
    #         meas = msg.body['DATA']['MEASUREMENTS']

    #         aitken = self.component_map['INSTRUMENTS']['aitken_dmps']['LIST'][0]
    #         accum = self.component_map['INSTRUMENTS']['accum_dmps']['LIST'][0]

    #         if id == aitken.get_id():

    #             if dt not in self.dmps_data:
    #                 self.dmps_data = dict()
    #                 self.dmps_data[dt] = dict()

    #             self.dmps_data[dt]['aitken'] = {
    #                 'dp': meas['diameter_um']['VALUE'],
    #                 'dn': meas['bin_concentration']['VALUE']
    #             }

    #         elif id == accum.get_id():

    #             if dt not in self.dmps_data:
    #                 self.dmps_data = dict()
    #                 self.dmps_data[dt] = dict()

    #             self.dmps_data[dt]['accum'] = {
    #                 'dp': meas['diameter_um']['VALUE'],
    #                 'dn': meas['bin_concentration']['VALUE']
    #             }

    #         if (
    #             dt in self.dmps_data and
    #             'aitken' in self.dmps_data[dt] and
    #             'accum' in self.dmps_data[dt]
    #         ):

    #             # save input file
    #             # ts = datetime.timestamp(datetime.now())
    #             ts = 101.1234  # place holder
    #             Tk = 293.15
    #             p = 1013.15
    #             num_bins = (
    #                 len(self.dmps_data[dt]['aitken']['dp']) +
    #                 len(self.dmps_data[dt]['accum']['dp'])
    #             )

    #             fn = './daq/controller/contrib/sizing/inversion/ein.dat'
    #             with open(fn, 'w') as f:
    #                 # write dp
    #                 f.write(f'{ts} {Tk} {p} {num_bins}')
    #                 for dp in self.dmps_data[dt]['aitken']['dp']:
    #                     f.write(f' {round(dp*1000, 2)}')
    #                 for dp in self.dmps_data[dt]['accum']['dp']:
    #                     f.write(f' {round(dp*1000, 2)}')
    #                 f.write('\n')

    #                 # write dn
    #                 f.write(f'{ts} {Tk} {p} {num_bins}')
    #                 for dn in self.dmps_data[dt]['aitken']['dn']:
    #                     f.write(f' {dn}')
    #                 for dn in self.dmps_data[dt]['accum']['dn']:
    #                     f.write(f' {dn}')
    #                 f.write('\n')

    #             # do inversion
    #             print(f'do inversion')

    #             inv = './main'
    #             res = subprocess.run(
    #                 [inv],
    #                 stdout=subprocess.DEVNULL,
    #                 cwd='./daq/controller/contrib/sizing/inversion'
    #             )
    #             print(f'inversion process result: {res}')

    #             # check res code

    #             # read output file
    #             fn = './daq/controller/contrib/sizing/inversion/out.dat'
    #             # out_dp = []
    #             # out_dndlogdp = []
    #             with open(fn, 'r') as f:
    #                 dp_line = f.readline()
    #                 dndlogdp_line = f.readline()

    #             dp_parts = dp_line.split()
    #             dndlogdp_parts = dndlogdp_line.split()

    #             dmps_dp = []
    #             dmps_dndlogdp = []
    #             # for dp, dn in zip(dp_parts, dndlogdp_parts):
    #             for i in range(4, len(dp_parts)):
    #                 dmps_dp.append(float(dp_parts[i])/1000)
    #                 dmps_dndlogdp.append(round(float(dndlogdp_parts[i]), 3))

    #             # dmps_dlogdp = math.pow(
    #             #     10,
    #             #     math.log10(dmps_dp[1]/dmps_dp[0])
    #             # )
    #             dmps_dlogdp = math.log10(dmps_dp[1]/dmps_dp[0])

    #             dmps_intN = 0
    #             for bin in dmps_dndlogdp:
    #                 dmps_intN += bin*dmps_dlogdp

    #             if dt not in self.data_ready:
    #                 self.data_ready = dict()
    #                 self.data_ready[dt] = dict()
    #             self.data_ready[dt]['dmps'] = {
    #                 'dmps_dndlogdp': {
    #                     'VALUE': dmps_dndlogdp
    #                 },
    #                 'dmps_diameter_um': {
    #                     'VALUE': dmps_dp
    #                 },
    #                 'dmps_integral_concentration': {
    #                     'VALUE': round(dmps_intN, 3)
    #                 }
    #             }

    #     if self.has_aps:
    #         meas = msg.body['DATA']['MEASUREMENTS']

    #         aps = self.component_map['INSTRUMENTS']['aps']['LIST'][0]
    #         if id == aps.get_id():

    #             aps_dp = meas['diameter_um']['VALUE']
    #             aps_dn = meas['bin_concentration']['VALUE']

    #             print(f'aps_dp[8] = {aps_dp[8]}')
    #             # aps_dlogdp = math.pow(
    #             #     10,
    #             #     math.log10(aps_dp[9]/aps_dp[8])
    #             # )
    #             aps_dlogdp = math.log10(aps_dp[9]/aps_dp[8])

    #             aps_dndlogdp = []
    #             aps_intN = 0
    #             for bin in aps_dn:
    #                 aps_dndlogdp.append(round(bin/aps_dlogdp, 3))
    #                 aps_intN += bin

    #             if dt not in self.data_ready:
    #                 self.data_ready = dict()
    #                 self.data_ready[dt] = dict()
    #             self.data_ready[dt]['aps'] = {
    #                 'aps_dndlogdp': {
    #                     'VALUE': aps_dndlogdp
    #                 },
    #                 'aps_diameter_um': {
    #                     'VALUE': aps_dp
    #                 },
    #                 'aps_integral_concentration': {
    #                     'VALUE': round(aps_intN, 3)
    #                 }
    #             }

    #     if (
    #         (self.has_aitken and self.has_accum and self.has_aps) and
    #         (
    #             dt in self.data_ready and
    #             'dmps' in self.data_ready[dt] and
    #             'aps' in self.data_ready[dt]
    #         )
    #     ):
    #         # return valid entry
    #         entry = {
    #             'DATA': {
    #                 'DATETIME': dt,
    #                 'MEASUREMENTS': dict()
    #             }
    #         }
    #         for name, rec in self.data_ready[dt]['dmps'].items():
    #             entry['DATA']['MEASUREMENTS'][name] = rec
    #         for name, rec in self.data_ready[dt]['aps'].items():
    #             entry['DATA']['MEASUREMENTS'][name] = rec

    #         if self.alias:
    #             entry['alias'] = self.alias

    #         return entry

    #     return None

    async def handle_control_action(self, control, value):
        pass
        if control and value is not None:
            if control == 'start_stop':
                if value == 'START':
                    self.start()
                elif value == 'STOP':
                    self.stop()
                    
            await super(SimpleTSController, self).handle_control_action(control, value)

    def get_definition_instance(self):
        return SimpleTSController.get_definition()

    def get_definition():
        definition = dict()
        definition['module'] = SimpleTSController.__module__
        definition['name'] = SimpleTSController.__name__
        definition['tags'] = [
       ]

        definition["component_map"] = {
            "INSTRUMENTS": {
                "default": {"LIST": [], "PRIMARY": None},
            }
        }

        return {'DEFINITION': definition}
        # DAQ.daq_definition['DEFINITION'] = definition
        # return DAQ.daq_definition
