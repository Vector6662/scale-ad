from trie import Trie, sampling
from pyecharts.charts import Tree
from pyecharts import options as opts
from queue import Queue, LifoQueue, PriorityQueue
from anomaly_detection import detect
# from cdf import detect
root = Trie('root')
# essential frame is <CONTENT>

file_path_BGL = './data/BGL/BGL_2k.log'  # reduced log for test
log_format_BGL = '<TAG><SEQ><DATE><COMPONENT1><TIMESTAMP><COMPONENT2><COMPONENT3><PRIORITY><LEVEL><CONTENT>'


file_path_HDFS = './data/HDFS/HDFS_2k.log'
log_format_HDFS = '<DATE><TIME><PID><LEVEL><COMPONENT><CONTENT>'

file_path = file_path_BGL
log_format = log_format_BGL

def gen_trie_graph(root: Trie, name: str, parent_id: int, data: dict):
    """
    generate a trie structure for the use of scaleAD-ui, vue echarts
    """
    data['nodes'].append({'id': parent_id+1, 'name': name, 'symbolSize': 15, 'category': 0})
    if root.isEnd:
        log_cluster_id = parent_id+1
        for log_cluster in root.logClusters:
            data['nodes'].append({'id': log_cluster_id+1, 'name': f'log_cluster({log_cluster.template})', 'value': len(log_cluster.logMessages), 'category': 1})
            data['links'].append({'source': parent_id+1, 'target': log_cluster_id+1})
            log_cluster_id = log_cluster_id + 1
        return parent_id + 1

    child_id = parent_id + 1
    for name, child in root.children.items():
        child_id = gen_trie_graph(child, name, child_id, data)
        data['links'].append({'source': parent_id+1, 'target': child_id})
    return parent_id+1


def django_interface():
    data = {'nodes': list(), 'links':list(), 'categories':[{'name':'A'}, {'name':'B'}]}
    gen_trie_graph(root, 'root', -1, data)
    return data

def gen_trie_structure(root: Trie, name: str):
    """
    visualize trie data structure for pyecharts
    """
    if root.isEnd:
        t = dict()
        t['name'] = root.name
        t['children'] = []
        for log_cluster in root.logClusters:
            t['children'] = [
                {'name': f'log_clu({log_cluster.template})', 'value': len(log_cluster.logMessages)},
                {'name': 'items', 'value': log_cluster.logMessages}
            ]
        return t
    data = dict()
    data['name'] = name
    data['children'] = list()
    for name, child in root.children.items():
        data['children'].append(gen_trie_structure(child, name))
    return data


def render_tree(file_name: str, data, tree_name='TDA display'):
    """
    render a tree based on pyecharts
    """
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


def reconstruct():
    root.reconstruct()
    data = gen_trie_structure(root, 'root-reconstructed')

    render_tree("tree-reconstructed.html", data, 'TDA reconstructed')


def process():
    from preprocess import gen_header, read_line
    from logs import LogMessage

    sampling(file_path, log_format)

    logMessageL = []
    headers = gen_header(log_format)
    for line in read_line(file_path):
        log_message = LogMessage()
        log_message.preprocess(headers, line)

        trie_node, log_cluster = root.insert(log_message)

        # TODO: LRU

        logMessageL.append(log_message)  # all log messages

    data = gen_trie_structure(root, 'root')

    render_tree("tree_top_bottom.html", data)

    with open('structure.json', 'w') as f:
        f.write(str(data))

    # start detection
    log_clusters = root.search_clusters_recurse()
    detect(log_clusters)


if __name__ == "__main__":
    process()
