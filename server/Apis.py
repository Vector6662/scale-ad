from django.http.response import HttpResponse
import json
from tda.main import django_interface

def tda_display(request):
    result = django_interface()
    result = json.dumps(result)
    return HttpResponse(result)