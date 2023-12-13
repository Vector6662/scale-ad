from trie import Trie, sampling
from pyecharts.charts import Tree
from pyecharts import options as opts
from queue import Queue, LifoQueue, PriorityQueue
from anomaly_detection import detect

file_path = '../data/BGL/BGL_2k.log'  # reduced log for test
root = Trie('root')
# essential frame is <CONTENT>
log_format = '<TAG><SEQ><DATE><COMPONENT1><TIMESTAMP><COMPONENT2><COMPONENT3><PRIORITY><LEVEL><CONTENT>'


def visualize_trie(root: Trie, name: str):
    if root.isEnd:
        t = dict()
        t['name'] = root.name
        t['children'] = []
        for log_cluster in root.logClusters:
            t['children'].append(
                {'name': f'logclu:{log_cluster.template[0:10]}...)', 'value': len(log_cluster.logMessages)}
            )
        return t
    data = dict()
    data['name'] = name
    data['children'] = list()
    for name, child in root.child.items():
        data['children'].append(visualize_trie(child, name))
    return data


def tree(file_name: str, data, tree_name='TDA display'):
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
    data = visualize_trie(root, 'root-reconstructed')

    tree("tree-reconstructed.html", data, 'TDA reconstructed')


def process():
    from preprocess import gen_header, read_line
    from logs import LogMessage

    sampling(file_path, log_format)

    logMessageL = []
    headers = gen_header(log_format)
    for line in read_line(file_path):
        log_message = LogMessage()
        log_message.preprocess(headers, line)

        node = root.insert(log_message)

        logMessageL.append(log_message)  # all log messages

    data = visualize_trie(root, 'root')

    tree("tree_top_bottom.html", data)

    # start detection
    log_clusters = root.search_clusters_recurse()
    detect([len(log_cluster.logMessages) for log_cluster in log_clusters])


if __name__ == "__main__":
    process()
