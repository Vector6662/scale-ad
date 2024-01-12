from anomaly_detection import detect_cdf
from config import file_path, log_format
from server_apis import render_pyecharts_tree
from trie import Trie, sampling

root = Trie('root')
logMessages = []

def reconstruct():
    root.reconstruct()
    render_pyecharts_tree("tree-reconstructed.html", root, 'TDA reconstructed')


def process():
    from utils import gen_header, read_line
    from log_structure import LogMessage

    sampling(file_path, log_format)

    headers = gen_header(log_format)
    for line in read_line(file_path):
        log_message = LogMessage()
        log_message.preprocess(headers, line)

        trie_node, log_cluster = root.insert(log_message)
        log_message.log_cluster = log_cluster  # refer to its parent

        # TODO: LRU, add the most frequently used log templates into LRU. only those templates are used in detect().
        #  Moreover there may be another thread to

        # TODO: there may be a fixed size list for logMessages, for this object are only used in Django server API, only part of log messages are been shown
        logMessages.append(log_message)  # all log messages

    data = render_pyecharts_tree("tree_top_bottom.html", root)

    with open('structure.json', 'w') as f:
        f.write(str(data))

    # start detection
    log_clusters = root.search_clusters_recurse()
    detect_cdf(log_clusters)


if __name__ == "__main__":
    process()
