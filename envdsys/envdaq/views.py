from django.shortcuts import render
from .models import InstrumentMask, Controller

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

def controller(request):
    # list needs to be filtered based on controller
    instrument_list = InstrumentMask.objects.all()
    # print(instrument_list)
    context = {'instrument_list': instrument_list}
    return render(request, 'envdaq/controller.html', context=context)
