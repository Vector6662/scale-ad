from logs import LogMessage
from server_apis import render_pyecharts_tree
from trie import Trie, sampling
from queue import Queue, LifoQueue, PriorityQueue

# from anomaly_detection import detect
from cdf import detect

from config import file_path, log_format

root = Trie('root')
logMessages = []

def reconstruct():
    root.reconstruct()
    render_pyecharts_tree("tree-reconstructed.html", root, 'TDA reconstructed')


def process():
    from preprocess import gen_header, read_line
    from logs import LogMessage

    sampling(file_path, log_format)

    headers = gen_header(log_format)
    for line in read_line(file_path):
        log_message = LogMessage()
        log_message.preprocess(headers, line)

        trie_node, log_cluster = root.insert(log_message)
        log_message.log_cluster = log_cluster  # refer to its parent

        # TODO: LRU

        logMessages.append(log_message)  # all log messages

    data = render_pyecharts_tree("tree_top_bottom.html", root)

    with open('structure.json', 'w') as f:
        f.write(str(data))

    # start detection
    log_clusters = root.search_clusters_recurse()
    detect(log_clusters)


if __name__ == "__main__":
    process()
