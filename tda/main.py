from trie import Trie
import preprocess as prepro
from pyecharts.charts import Tree
from pyecharts import options as opts
from queue import Queue, LifoQueue, PriorityQueue

file_path = '../data/BGL/BGL_small.log'  # reduced log for test
root = Trie()
# essential frame is <CONTENT>
log_format = '<TAG><SEQ><DATE><COMPONENT1><TIMESTAMP><COMPONENT2><COMPONENT3><PRIORITY><LEVEL><CONTENT>'


def visualize_trie(root: Trie, name: str):
    if root.isEnd:
        ret = []
        for log_cluster in root.logClusters:
            t = dict()
            t['name'] = f'log_cluster_{log_cluster.__hash__()}'
            log_messages = log_cluster.logMessages
            t['value'] = len(log_messages)
            ret.append(t)
            return ret
    internal_data = dict()
    internal_data['name'] = name
    internal_data['children'] = list()
    for key, value in root.child.items():
        if value.isEnd:
            internal_data['children'] = visualize_trie(value, key)
        else:
            internal_data['children'].append(visualize_trie(value, key))
    return internal_data


if __name__ == "__main__":
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
