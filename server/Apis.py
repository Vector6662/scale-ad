from django.http.response import HttpResponse
from django.http.request import HttpRequest
import json
from tda.render_structure import django_interface
from tda.main import root


def trie_display_graph(request: HttpRequest):
    render_type = request.GET.get('render_type')
    result = django_interface(root, render_type)
    result = json.dumps(result)
    return HttpResponse(result)
