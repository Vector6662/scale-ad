from preprocess import LogMessage
from collections import OrderedDict

domain_knowledge = ['INFO', 'FATAL', 'ERROR', 'core']

stopwords = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves', 
             'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 
             'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 
             'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 
             'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 
             'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 
             'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 
             'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 
             'very', 'can', 'will', 'just', 'don', 'should', 'now']

K = 3 # 𝐾 most frequent tokens
token_occurrences = dict()

d=3 # their first 𝑑 prefix tokens

cmax=3 # hyper-parameter to limit the maximum number of child nodes

def traverse_d_k(log: LogMessage) -> str:
    '''
    Traverse by domain knowledge
    '''
    # TODO similarity in nlp?
    for knowledge in domain_knowledge:
        if knowledge in log.tokens:
            return knowledge
    return 'DEFAULT'

def traverse_m_f(log: LogMessage)->str:
    '''
    Traverse by most frequent tokens. English stopwords are discarded'''
    for token in log.tokens:
        token_occurrences[token] = token_occurrences.get(token, 0)+1
    list = sorted(token_occurrences.items(), key=lambda s:s[1], reverse=True)[0:K][1]
    return str(list)

def traverse_prefix(log: LogMessage)->str:
    '''
    Traverse by prefix tokens'''
    return 'DEFAULT'
    
    
    

traverse_funcs = [traverse_d_k, traverse_m_f, traverse_prefix]

class Trie:
    def __init__(self) -> None:
        self.child = dict()
        self.is_end = False
    
    # def searchPrefix(self, tokens:list(str)):
    #     node = self
    #     for str in tokens:
    #         if not node.child[str]:
    #             return None
    #         node = node.child[str]
    #     return node

    def insert(self, log: LogMessage):
        node = self
        for func in traverse_funcs:
            st = func(log)
            if st not in node.child:
                node.child[st] = Trie()
            node = node.child[st]
            node.is_end = False
        node.is_end = True
    
    # def search(self, tokens:list(str)):
    #     node = self.searchPrefix(tokens)
    #     return node is not None and node.is_end

    