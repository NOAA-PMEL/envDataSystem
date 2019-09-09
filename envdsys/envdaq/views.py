from django.shortcuts import render
from .models import InstrumentAlias, Controller
from django.utils.safestring import mark_safe
import json
from bokeh.embed import server_document
from plots.plots import PlotManager


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


def controller(request, controller_name):
    # list needs to be filtered based on controller
    # instrument_list = InstrumentMask.objects.all()
    # print(instrument_list)
    # context = {'instrument_list': instrument_list}

    # TODO: lookup controller name in Models pass config/def in context
    #       what to do if not in db?

    print(f'controller_name: {mark_safe(json.dumps(controller_name))}')
    context = {
        'controller_name': mark_safe(json.dumps(controller_name)),
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
        alias.instrument.definition.measurement_config.config)

    plots = dict()
    plots["host"] = "localhost"
    plots["port"] = 5001
    plots["name"] = "/instrument_"+alias.name

    
    # TODO: these values need to got into database as runtime
    #       data?
    print(f'{PlotManager.get_app_list(alias.name)}')
    plots["app_list"] = PlotManager.get_app_list(alias.name)
    print(f'{plots["app_list"]}')
    plot_scripts = []
    for app in plots['app_list']:
        plot_scripts.append(
            server_document("http://localhost:5001"+app)
        )
    
    # TODO: get plot name dynamically
    plot_script = server_document("http://localhost:5001"+plots["name"])
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
