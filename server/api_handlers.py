from django.http.response import HttpResponse
from django.http.request import HttpRequest
import json
from tda.server_apis import render_echarts_api, expert_feedback_api
from tda.process_tda import root, logMessages


def api_test(request):
    return HttpResponse('hello')


def trie_display_graph(request: HttpRequest):
    render_type = request.GET.get('render_type')
    result = render_echarts_api(root, render_type)
    result = json.dumps(result)
    return HttpResponse(result)


def log_feedback(request: HttpRequest):
    data = expert_feedback_api(root)
    data = json.dumps(data)
    return HttpResponse(data)


def log_messages_result(request: HttpRequest):
    """

    """
    data = [{'log': log_message.line, 'decision': log_message.parent.feedback.decision,
             'reason': log_message.parent.feedback.reason} for log_message in logMessages]
    data = json.dumps(data)
    return HttpResponse(data)
