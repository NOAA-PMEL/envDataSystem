from django.shortcuts import render
from .models import InstrumentAlias, Controller
from django.utils.safestring import mark_safe
import json
from bokeh.embed import server_document
from plots.plots import PlotManager
from django.conf import settings


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
    return render(request, 'envdaq/index.html', {})


def daqserver(request):
    # TODO: This will be based on current "Project"

    # list needs to be filtered based on controller
    # instrument_list = InstrumentMask.objects.all()
    # print(instrument_list)
    # context = {'instrument_list': instrument_list}

    # context = {
    #     'controller_name_json': mark_safe(json.dumps(controller_name))
    # }
    return render(request, 'envdaq/daqserver.html')


def controller(request, controller_alias_name):

    print(f'{settings.ALLOWED_HOSTS}')
    # list needs to be filtered based on controller
    # instrument_list = InstrumentMask.objects.all()
    # print(instrument_list)
    # context = {'instrument_list': instrument_list}

    # TODO: lookup controller name in Models pass config/def in context
    #       what to do if not in db?
    try:
        ctr = Controller.objects.get(alias_name=controller_alias_name)
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

    plots = dict()
    plots["host"] = host
    plots["port"] = port
    plots["name"] = "/controller_"+ctr.alias_name

    print(f'{PlotManager.get_app_list(ctr.alias_name)}')
    plots["app_list"] = PlotManager.get_app_list(ctr.alias_name)
    plot_scripts = []
    for app in plots['app_list']:
        plot_scripts.append(
            server_document(f"http://{host}:{port}"+app)
        )
    # plot_script = server_document("http://localhost:5001"+plots["name"])
    # print(f'plot_script: {plot_script}')
    print(f'565656 plot_scripts: {plot_scripts}')
    print(f'controller_name: {mark_safe(json.dumps(ctr.name))}')
    context = {
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


def instrument(request, instrument_name):
    # list needs to be filtered based on controller
    # instrument_list = InstrumentMask.objects.all()
    # print(instrument_list)
    # context = {'instrument_list': instrument_list}

    # TODO: lookup controller name in Models pass config/def in context
    #       what to do if not in db?

    try:
        alias = InstrumentAlias.objects.get(name=instrument_name)

        print(f'alias: {alias}')
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

    plots = dict()
    plots["host"] = host
    plots["port"] = port
    plots["name"] = "/instrument_"+alias.name

    
    # TODO: these values need to got into database as runtime
    #       data?
    print(f'{PlotManager.get_app_list(alias.name)}')
    plots["app_list"] = PlotManager.get_app_list(alias.name)
    print(f'{plots["app_list"]}')
    plot_scripts = []
    for app in plots['app_list']:
        plot_scripts.append(
            server_document(f"http://{host}:{port}"+app)
        )
    
    # TODO: get plot name dynamically
    plot_script = server_document(f"http://{host}:{port}"+plots["name"])
    print(f'plot_scripts: {plot_scripts}')
    context = {
        'instrument_instance': mark_safe(
            json.dumps(alias.instrument.definition.__str__())
        ),
        'instrument_name': mark_safe(json.dumps(instrument_name)),
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
