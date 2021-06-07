from django.shortcuts import render
# from .models import InstrumentAlias, Controller
from django.utils.safestring import mark_safe
# import json
# from bokeh.embed import server_document
# from plots.plots import PlotManager
from django.conf import settings
from shared.data.namespace import Namespace
from envnet.models import Network, DAQRegistration, ServiceRegistration


def index(request):


    net_map = {}
    networks = Network.objects.all()
    for net in networks:
        net_map[net.name] = {
            "description": net.description,
            "active": net.active
        }

    daq_reg_map = {}
    daq_regs = DAQRegistration.objects.all()
    for reg in daq_regs:
        ns = Namespace().from_dict(reg.namespace)

        daq_reg_map[ns.get_namespace()] = {
            "host": ns.get_host(),
            "name": ns.name,
            # "signature": ns.get_namespace_sig(),
            "type": reg.daq_type,
            # "status": reg.status
        }
        # daq_reg_map[reg.reg_id] = {
        #     "type": reg.daq_type,
        #     "status": reg.status
        # }



    context = {
        "network_map": net_map,
        "daq_reg_map": daq_reg_map,
    }


    return render(request, 'index.html', context)
