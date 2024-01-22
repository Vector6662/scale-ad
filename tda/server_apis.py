"""
APIs exposed to Django server.
generate json structure for rendering;
data from expert feedbacks;
"""
from datetime import datetime

from trie import Trie
from pyecharts.charts import Tree
from pyecharts import options as opts


def gen_trie_graph(root: Trie, name: str, total_id: int, data: dict):
    """
    generate a trie json structure for the use of scaleAD-ui, vue lib echarts(type: "graph")
    return: cur_id, current node id; total_id: total number of id that has been used.
    json format:
    {
        "nodes": [
            {"id": 0,"name": "root", "symbolSize": 10, "category": 0}, {"id": 1, "name": "INFO", "symbolSize": 10, "category": 0}
        ],
        "links": [{"source": 0, "target": 1}],
        "categories": [{"name": "A"}, {"name": "B"}]
    }
    """
    cur_id = total_id + 1
    data['nodes'].append({'id': cur_id, 'name': name, 'symbolSize': 20, 'category': 0})
    if root.isEnd:
        log_cluster_id = cur_id + 1
        for log_cluster in root.logClusters:
            data['nodes'].append({'id': log_cluster_id, 'name': f'log_cluster({log_cluster.template})',
                                  'value': len(log_cluster.logMessagesCache), 'symbolSize': 10, 'category': 1})
            data['links'].append({'source': cur_id, 'target': log_cluster_id})
            log_cluster_id = log_cluster_id + 1
        return cur_id, log_cluster_id - 1

    total_id = cur_id
    for name, child in root.children.items():
        child_id, total_id = gen_trie_graph(child, name, total_id, data)
        data['links'].append({'source': cur_id, 'target': child_id})
    return cur_id, total_id


def gen_trie_tree(root: Trie, name: str, debug=False):
    """
    visualize trie data structure for pyecharts type "tree".
    if debug==True, each leaf node will list all log messages under the log cluster,
    else, only total amounts of log messages under this log cluster, because frontend frameworks(eg. pyecharts, echarts) only support integer in field 'value'.
    json format, see structure.json

    """
    if root.isEnd:
        t = dict()
        t['name'] = root.name
        t['children'] = []
        for log_cluster in root.logClusters:
            if debug:  # just for debug: see json structure details(structure.json) intuitively
                items = '\n'.join(log_cluster.logMessagesCache)
                t['children'] = [{'name': f'{log_cluster.template}',
                                  'value': f'{log_cluster.logMessagesCache}'}]
            else:
                t['children'] = [{'name': f'{log_cluster.template}',
                                  'value': len(log_cluster.logMessagesCache)}]
        return t
    data = dict()
    data['name'] = name
    data['children'] = list()
    for name, child in root.children.items():
        data['children'].append(gen_trie_tree(child, name, debug))
    return data


def render_pyecharts_tree(file_name: str, root: Trie, tree_name='TDA display'):
    """
    render a tree display, based on pyecharts
    """
    data = gen_trie_tree(root, tree_name, debug=True)
    tree = (
        Tree()
        .add(
            "",
            [data],
            collapse_interval=2,
            orient="TB",
            label_opts=opts.LabelOpts(
                position="top",
                horizontal_align="right",
                vertical_align="middle",
                rotate=-90,
            ),
            is_roam=True,
            pos_left='center',
            symbol_size=10,
            initial_tree_depth=3,
        )
        .set_global_opts(title_opts=opts.TitleOpts(title=tree_name))
    ).render(file_name)
    return data

# APIs below:

def render_echarts_api(root: Trie, render_type='graph'):
    """
    api exposed to Django server to render trie tree or graph
    render_type: graph or tree
    """
    assert render_type == 'graph' or 'tree'
    data = {}

    if render_type == 'graph':
        data = {'nodes': list(), 'links': list(), 'categories': [{'name': 'Internal Nodes'}, {'name': 'Leaf Nodes'}]}
        gen_trie_graph(root, 'root', -1, data)
    elif render_type == 'tree':
        data = gen_trie_tree(root, 'Trie display', debug=False)
    return data


def expert_feedback_api(root: Trie):
    data = []
    for log_cluster in root.search_clusters_recurse():
        if log_cluster.feedback is None:
            continue
        data.append({
            'log_template': log_cluster.template,
            'level': log_cluster.feedback.decision,
            'ep': log_cluster.feedback.ep,
            'tp': log_cluster.feedback.tp,
            'logs': log_cluster.get_log_messages(),
            'desc': log_cluster.feedback.reason
        })
    return data  # for debug

