from django.shortcuts import render
# from .models import InstrumentAlias, Controller
from django.utils.safestring import mark_safe
# import json
# from bokeh.embed import server_document
# from plots.plots import PlotManager
from django.conf import settings
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
        daq_reg_map[reg.namespace] = {
            "type": reg.daq_type,
            "status": reg.status
        }



    context = {
        "network_map": net_map,
        "daq_reg_map": daq_reg_map,
        # "pdsglobals": pdsglobals,
        # "coordvarformset": coordvarformset,
        # "varformset": varformset,
        # "project_label": project_label,
        # "base_dataset_label": base_dataset_label,
        # "project_dataset_label": project_dataset.name,
        # "coord_variable_list": [var.name for var in list(coord_variable_list)],
        # "variable_list": [var.name for var in list(variable_list)],
        # "error": None,
    }


    return render(request, 'index.html', context)
