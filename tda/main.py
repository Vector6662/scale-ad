from render_structure import render_pyecharts_tree
from trie import Trie, sampling
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


def reconstruct():
    root.reconstruct()
    render_pyecharts_tree("tree-reconstructed.html", root, 'TDA reconstructed')


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

    data = render_pyecharts_tree("tree_top_bottom.html", root)

    with open('structure.json', 'w') as f:
        f.write(str(data))

    # start detection
    log_clusters = root.search_clusters_recurse()
    detect(log_clusters)


if __name__ == "__main__":
    process()
