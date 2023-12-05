from trie import Trie
import preprocess as prepro
from pyecharts.charts import Tree
from pyecharts import options as opts
from queue import Queue,LifoQueue,PriorityQueue


file_path = '../data/BGL/BGL_small.log'
root = Trie()
# essential frame is <CONTENT>
log_format = '<TAG><SEQ><DATE><COMPONENT1><TIMESTAMP><COMPONENT2><COMPONENT3><PRIORITY><LEVEL><CONTENT>'

def visualize_trie(root:Trie, name:str):
    data = dict()
    data['name'] = name
    data['children'] = list()
    for key, value in root.child.items():
        data['children'].append(visualize_trie(value, key))
    return data

            
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
        Tree().add(
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
            )
    ).render("tree_top_bottom.html")


    
    