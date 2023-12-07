from trie import Trie
import preprocess as prepro
from pyecharts.charts import Tree
from pyecharts import options as opts
from queue import Queue, LifoQueue, PriorityQueue

file_path = '../data/BGL/BGL_small.log'  # reduced log for test
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
                {'name': f'log_cluster_{log_cluster.__hash__()}', 'value': len(log_cluster.logMessages)}
            )
        return t
    data = dict()
    data['name'] = name
    data['children'] = list()
    for name, child in root.child.items():
            data['children'].append(visualize_trie(child, name))
    return data


def process():
    headers = prepro.gen_header(log_format)
    logMessageL = []
    for line in prepro.read_line(file_path):
        log_message = prepro.LogMessage()
        log_message.preprocess(headers, line)

        node = root.insert(log_message)

        logMessageL.append(log_message)  # all log messages

    data = visualize_trie(root, 'root')
    tree = (
        Tree()
        .add(
            "TDA display",
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
        .set_global_opts(title_opts=opts.TitleOpts(title="TDA-Display"))

    ).render("tree_top_bottom.html")


if __name__ == "__main__":
    process()
