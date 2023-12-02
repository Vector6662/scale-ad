from trie import Trie
import preprocess as prepro
from pyecharts.charts import Tree
from pyecharts import options as opts
from queue import Queue,LifoQueue,PriorityQueue


file_path = 'data/BGL/BGL_small.log'
root = Trie()


def visualze_trie(root:Trie, name:str):
    data = dict()
    data['name'] = name
    data['children'] = list()
    childs = root.child
    for key, value in childs.items():
        data['children'].append(visualze_trie(value, key))
    # queue = Queue()
    # queue.put(root)
    # while(queue.empty()):
    #     size = queue.qsize()
    #     for _ in range(size):
    #         node = queue.get()
    #         childs = node.child
    #         for key, value in childs.items():
    #             data['children'].append(visualze_trie(value, key))
    return data

            
if __name__ == "__main__":
    for line in prepro.read_line(file_path):
        log = prepro.tokenize(line)
        # print('tokenized:', log)
        root.insert(log)
    data = visualze_trie(root, 'root')
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
            )
    ).render("tree_top_bottom.html")


    
    