from django.shortcuts import render
from .models import Tag

# Create your views here.


def index(request):

    tag_list = Tag.objects.filter(type=None)
    inst_type_list = Tag.objects.filter(type='INSTRUMENT_TYPE')

    context = {
        'tag_list': tag_list,
        'inst_type_list': inst_type_list,
    }
    return render(request, 'envtags/index.html', context)
