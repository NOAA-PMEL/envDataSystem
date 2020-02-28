from daq.instrument.instrument import Instrument
from data.message import Message
from daq.daq import DAQ
import asyncio
from utilities.util import time_to_next
from daq.interface.interface import Interface
# from plots.plots import PlotManager
# from plots.apps.plot_app import TimeSeries1D


class DMTInstrument(Instrument):

    INSTANTIABLE = False

    def __init__(self, config, **kwargs):
        # def __init__(
        #     self,
        #     config,
        #     ui_config=None,
        #     auto_connect_ui=True
        # ):

        super(DMTInstrument, self).__init__(config, **kwargs)

        self.mfg = 'DMT'

    def setup(self):
        super().setup()

        # TODO: add properties get/set to interface for
        #       things like readmethod

