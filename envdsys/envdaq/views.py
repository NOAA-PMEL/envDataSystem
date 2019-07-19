from django.shortcuts import render
from .models import InstrumentMask, Controller
from django.utils.safestring import mark_safe
import json


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
        'controller_name_json': mark_safe(json.dumps(controller_name))
    }
    return render(request, 'envdaq/controller.html', context=context)
