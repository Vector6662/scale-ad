from django.http.response import HttpResponse
from django.http.request import HttpRequest
import json
from tda.server_apis import render_api, expert_feedback_api
from tda.process_tda import root, logMessages


def api_test(request):
    return HttpResponse('hello')


def trie_display_graph(request: HttpRequest):
    render_type = request.GET.get('render_type')
    result = render_api(root, render_type)
    result = json.dumps(result)
    return HttpResponse(result)


def log_feedback(request: HttpRequest):
    data = expert_feedback_api(root)
    data = json.dumps(data)
    return HttpResponse(data)

def log_messages_result(request: HttpRequest):
    """

    """
    data = [{'log': log.line, 'decision': log.log_cluster.feedback.decision, 'reason': log.log_cluster.feedback.reason} for log in logMessages]
    data = json.dumps(data)
    return HttpResponse(data)