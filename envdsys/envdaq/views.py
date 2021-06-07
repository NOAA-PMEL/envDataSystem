from django.http.response import Http404
from django.shortcuts import get_object_or_404, render

from envtags.models import Configuration
from .models import DAQController, DAQInstrument, InstrumentAlias, Controller
from django.utils.safestring import mark_safe
import json
from bokeh.embed import server_document
from plots.plots import PlotManager
from django.conf import settings
from envnet.models import DAQRegistration


# # Create your views here.
# from django.http import HttpResponse
#
#
# def index(request):
#
#     return HttpResponse("Hello, world. You're at the envDAQ page.")
#
# # chat/views.py
# from django.shortcuts import render

def index(request):

    # print(f"request: {request}")
    # try:
    #     regs = DAQRegistration.objects.all()
    #     print(f'regs: {regs}')

    # except DAQRegistration.DoesNotexist:
    #     # TODO: return 404 ... lookup how
    #     pass
    #     regs = []

    # daq_registration_map = {}
    # if regs:
    #     for reg in regs:
    #         # daq_registration_map[reg["namespace"]] = {

    #         # }

    #         daq_registration_map[reg.namespace] = reg.get_registration()
    #         # {
    #         #     "config": json.loads(reg.config),
    #         #     "status": reg.status
    #         # }
    #         # print(f"reg: {reg.get_registration()}")

    # context = {
    #     "daq_map": daq_registration_map,
    # }
    # print(f"context: {context}")
    context = {}
    return render(request, 'envdaq/index.html', context=context)


def daqserver(request, daq_host, daq_namespace):
    # TODO: This will be based on current "Project"

    # print(f'%%%%% request: {request}')

    # get list of available configurations
    # config_list = []
    # try:
    #     configs = Configuration.objects.all()
    #     for config in configs:
    #         try:
    #             cfg = json.loads(config.config)
    #             if "ENVDAQ" in cfg:
    #                 config_list.append(config.config)
    #         except TypeError:
    #             pass
    # except Configuration.DoesNotExist:
    #     pass

    # list needs to be filtered based on controller
    # instrument_list = InstrumentMask.objects.all()
    # print(instrument_list)
    # context = {'instrument_list': instrument_list}

    context = {
        'daq_host': daq_host,
        'daq_namespace': daq_namespace,
        # 'config_list': config_list,
    }
    return render(request, 'envdaq/daqserver.html', context=context)

def daq_controller(request, daq_host, parent_namespace, controller_namespace):

    daq_controller = None
    controllers = DAQController.objects.filter(name=controller_namespace)
    # controllers = get_object_or_404(DAQController, name=controller_namespace)
    get_object_or_404(controllers)

    for controller in controllers:
        ns = controller.get_namespace()
        parent_sig = ns.get_namespace_sig(section="PARENT")

        if (
            parent_sig["host"] == daq_host
            and parent_sig["namespace"] == parent_namespace
        ):
            daq_controller = controller
            controller_ns = ns
            break        
    
    if not daq_controller:
        raise Http404(f"DAQController {controller_namespace} not found")

    measurements = daq_controller.measurement_sets

    # server_sig = controller_ns.get_namespace_comp_sig()
    plotserver_sig = PlotManager.get_server(server_id=ns).get_sig()
    plotserver_host = plotserver_sig["host"]
    plotserver_port = plotserver_sig["port"]
    print(f"plotserver_sig: {plotserver_sig}")

    plotserver_ui_host = plotserver_host
    if 'ui_host' in settings.PLOT_SERVER:
        plotserver_ui_host = settings.PLOT_SERVER['ui_host']

    request_host = request.get_host().split(":")[0]
    if request_host != plotserver_ui_host:
        plotserver_ui_host = request_host
        
    # host = 'localhost'
    # port = 5001
    # if 'server_id' in settings.PLOT_SERVER:
    #     host = settings.PLOT_SERVER['server_id'][0]
    #     port = settings.PLOT_SERVER['server_id'][1]

    # if 'hostname' in settings.PLOT_SERVER:
    #     host = settings.PLOT_SERVER['hostname']

    # test_host = request.get_host()
    print(f"++++ hosts: {plotserver_host}:{plotserver_port}, {plotserver_ui_host}:{plotserver_port}")
    plots = dict()
    # plots["host"] = host
    # plots["port"] = port
    plots["host"] = plotserver_ui_host
    plots["port"] = plotserver_port
    plots["name"] = "/controller_"+daq_controller.name

    # print(f"views plots: {plots}, {host}, {port}, {plotserver_host}, {plotserver_port}")
    # print(f'{PlotManager.get_app_list(ctr.alias_name)}')
    plots["app_list"] = PlotManager.get_app_list(daq_controller.name)
    plot_scripts = []
    for app in plots['app_list']:
        plot_scripts.append(
            # server_document(f"http://{host}:{port}"+app)
            server_document(f"http://{plotserver_ui_host}:{plotserver_port}"+app)
        )
    # plot_script = server_document("http://localhost:5001"+plots["name"])
    # print(f'plot_script: {plot_script}')
    # print(f'565656 plot_scripts: {plot_scripts}')
    # print(f'controller_name: {mark_safe(json.dumps(ctr.name))}')
    context = {
        'daq_host': mark_safe(daq_host),
        'parent_namespace': mark_safe(parent_namespace),
        # 'daq_namespace': mark_safe(json.dumps(daq_namespace)),
        'controller_namespace': mark_safe(controller_namespace),
        'controller_display_name': mark_safe(daq_controller.name),
        'controller_name': mark_safe(json.dumps(daq_controller.name)),
        'controller_label': mark_safe(json.dumps(daq_controller.name)),
        'controller_measurements': mark_safe(
            json.dumps(measurements)
        ),
        'plot_app': mark_safe(json.dumps(plots)),
        # 'plot_scriocat': plot_script,
        'plot_scripts': plot_scripts,
    }
    return render(request, 'envdaq/controller.html', context=context)


def controller(request, daq_host, parent_namespace, controller_namespace):

    # print(f'{settings.ALLOWED_HOSTS}')
    # list needs to be filtered based on controller
    # instrument_list = InstrumentMask.objects.all()
    # print(instrument_list)
    # context = {'instrument_list': instrument_list}

    # TODO: lookup controller name in Models pass config/def in context
    #       what to do if not in db?
    try:
        ctr = Controller.objects.get(alias_name=controller_namespace)
        print(f'controller: {ctr}')
    except Controller.DoesNotexist:
        # TODO: return 404 ... lookup how
        pass
    
    # TODO: have function that gets 'tree' config for 
    #       every view
    # instruments = ctr.get_instruments()
    # get instrument names for links

    measurements = json.loads(
        ctr.measurement_config.config
    )
    host = 'localhost'
    port = 5001
    if 'server_id' in settings.PLOT_SERVER:
        host = settings.PLOT_SERVER['server_id'][0]
        port = settings.PLOT_SERVER['server_id'][1]

    if 'hostname' in settings.PLOT_SERVER:
        host = settings.PLOT_SERVER['hostname']

    plots = dict()
    plots["host"] = host
    plots["port"] = port
    plots["name"] = "/controller_"+ctr.alias_name

    # print(f'{PlotManager.get_app_list(ctr.alias_name)}')
    plots["app_list"] = PlotManager.get_app_list(ctr.alias_name)
    plot_scripts = []
    for app in plots['app_list']:
        plot_scripts.append(
            server_document(f"http://{host}:{port}"+app)
        )
    # plot_script = server_document("http://localhost:5001"+plots["name"])
    # print(f'plot_script: {plot_script}')
    # print(f'565656 plot_scripts: {plot_scripts}')
    # print(f'controller_name: {mark_safe(json.dumps(ctr.name))}')
    context = {
        'parent_namepace': mark_safe(json.dumps(parent_namespace)),
        # 'daq_namespace': mark_safe(json.dumps(daq_namespace)),
        'controller_namespace': mark_safe(json.dumps(controller_namespace)),
        'controller_display_name': mark_safe(json.dumps(ctr.name)),
        'controller_name': mark_safe(json.dumps(ctr.alias_name)),
        'controller_label': mark_safe(json.dumps(ctr.name)),
        'controller_measurements': mark_safe(
            json.dumps(measurements)
        ),
        'plot_app': mark_safe(json.dumps(plots)),
        # 'plot_scriocat': plot_script,
        'plot_scripts': plot_scripts,
    }
    return render(request, 'envdaq/controller.html', context=context)

def daq_instrument(request, daq_host, parent_namespace, instrument_namespace):
    daq_instrument = None
    instruments = DAQInstrument.objects.filter(name=instrument_namespace)
    # controllers = get_object_or_404(DAQController, name=controller_namespace)
    get_object_or_404(instruments)

    for instrument in instruments:
        ns = instrument.get_namespace()
        parent_sig = ns.get_namespace_sig(section="PARENT")

        if (
            parent_sig["host"] == daq_host
            and parent_sig["namespace"] == parent_namespace
        ):
            daq_instrument = instrument
            break        
    
    if not daq_instrument:
        raise Http404(f"DAQInstrument {instrument_namespace} not found")

    measurements = daq_instrument.measurement_sets

    # server_sig = controller_ns.get_namespace_comp_sig()
    plotserver_sig = PlotManager.get_server(server_id=ns).get_sig()
    plotserver_host = plotserver_sig["host"]
    plotserver_port = plotserver_sig["port"]
    print(f"plotserver_sig: {plotserver_sig}")

    plotserver_ui_host = plotserver_host
    if 'ui_host' in settings.PLOT_SERVER:
        plotserver_ui_host = settings.PLOT_SERVER['ui_host']

    request_host = request.get_host().split(":")[0]
    if request_host != plotserver_ui_host:
        plotserver_ui_host = request_host

    # host = 'localhost'
    # port = 5001
    # if 'server_id' in settings.PLOT_SERVER:
    #     host = settings.PLOT_SERVER['server_id'][0]
    #     port = settings.PLOT_SERVER['server_id'][1]

    # if 'hostname' in settings.PLOT_SERVER:
    #     host = settings.PLOT_SERVER['hostname']

    print(f"++++ hosts: {plotserver_host}:{plotserver_port}, {plotserver_ui_host}:{plotserver_port}")
    plots = dict()
    # plots["host"] = host
    # plots["port"] = port
    plots["host"] = plotserver_ui_host
    plots["port"] = plotserver_port
    plots["name"] = "/instrument_"+daq_instrument.name

    
    # TODO: these values need to got into database as runtime
    #       data?
    # print(f'{PlotManager.get_app_list(alias.name)}')
    plots["app_list"] = PlotManager.get_app_list(daq_instrument.name)
    # print(f'{plots["app_list"]}')
    plot_scripts = []
    for app in plots['app_list']:
        plot_scripts.append(
            # server_document(f"http://{host}:{port}"+app)
            server_document(f"http://{plotserver_ui_host}:{plotserver_port}"+app)
        )
    
    # TODO: get plot name dynamically
    # plot_script = server_document(f"http://{host}:{port}"+plots["name"])
    plot_script = server_document(f"http://{plotserver_ui_host}:{plotserver_port}"+plots["name"])
    print(f'plot_scripts: {plot_scripts}')
    context = {
        # 'daq_namespace': mark_safe(json.dumps(daq_namespace)),
        # 'controller_namespace': mark_safe(json.dumps(controller_namespace)),
        'daq_host': mark_safe(daq_host),
        'parent_namespace': mark_safe(parent_namespace),
        'instrument_namespace': mark_safe(instrument_namespace),
        'instrument_instance': mark_safe(
            json.dumps(f"{instrument.instrument}")
        ),
        'instrument_name': mark_safe(json.dumps(instrument_namespace)),
        'instrument_label': mark_safe(json.dumps(daq_instrument.name)),
        'instrument_prefix': mark_safe(json.dumps(daq_instrument.name)),
        'instrument_measurements': mark_safe(
            json.dumps(measurements)
        ),
        'plot_app': mark_safe(json.dumps(plots)),
        'plot_script': plot_script,
        'plot_scripts': plot_scripts,
    }
    # print(f'context: {context}')

    return render(request, 'envdaq/instrument.html', context=context)

# def instrument(request, daq_namespace, controller_namespace, instrument_namespace):
def instrument(request, parent_namespace, instrument_namespace):
    # list needs to be filtered based on controller
    # instrument_list = InstrumentMask.objects.all()
    # print(instrument_list)
    # context = {'instrument_list': instrument_list}

    # TODO: lookup controller name in Models pass config/def in context
    #       what to do if not in db?

    try:
        alias = InstrumentAlias.objects.get(name=instrument_namespace)

        # print(f'alias: {alias}')
    except InstrumentAlias.DoesNotExist:
        # TODO: return 404 ... lookup how
        pass

    # print(f'def = {alias.instrument.definition.__str__()}')
    # print(f'instrument_name: {mark_safe(json.dumps(instrument_name))}')
    # print(
    #     f'measurements: {alias.instrument.definition.measurement_config.config}')
    # measurements = str(alias.instrument.definition.measurement_config.config)
    # print(f'meas: {json.dumps(measurements)}')
    measurements = json.loads(
        alias.instrument.definition.measurement_config.config
    )

    host = 'localhost'
    port = 5001
    if 'server_id' in settings.PLOT_SERVER:
        host = settings.PLOT_SERVER['server_id'][0]
        port = settings.PLOT_SERVER['server_id'][1]

    if 'hostname' in settings.PLOT_SERVER:
        host = settings.PLOT_SERVER['hostname']

    plots = dict()
    plots["host"] = host
    plots["port"] = port
    plots["name"] = "/instrument_"+alias.name

    
    # TODO: these values need to got into database as runtime
    #       data?
    # print(f'{PlotManager.get_app_list(alias.name)}')
    plots["app_list"] = PlotManager.get_app_list(alias.name)
    # print(f'{plots["app_list"]}')
    plot_scripts = []
    for app in plots['app_list']:
        plot_scripts.append(
            server_document(f"http://{host}:{port}"+app)
        )
    
    # TODO: get plot name dynamically
    plot_script = server_document(f"http://{host}:{port}"+plots["name"])
    print(f'plot_scripts: {plot_scripts}')
    context = {
        # 'daq_namespace': mark_safe(json.dumps(daq_namespace)),
        # 'controller_namespace': mark_safe(json.dumps(controller_namespace)),
        'parent_namespace': mark_safe(json.dumps(parent_namespace)),
        'instrument_namespace': mark_safe(json.dumps(instrument_namespace)),
        'instrument_instance': mark_safe(
            json.dumps(alias.instrument.definition.__str__())
        ),
        'instrument_name': mark_safe(json.dumps(instrument_namespace)),
        'instrument_label': mark_safe(json.dumps(alias.label)),
        'instrument_prefix': mark_safe(json.dumps(alias.prefix)),
        'instrument_measurements': mark_safe(
            json.dumps(measurements)
        ),
        'plot_app': mark_safe(json.dumps(plots)),
        'plot_script': plot_script,
        'plot_scripts': plot_scripts,
    }
    # print(f'context: {context}')

    return render(request, 'envdaq/instrument.html', context=context)
