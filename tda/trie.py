
domain_knowledge = ['INFO', 'FATAL', 'ERROR']

class Trie:
    def __init__(self) -> None:
        self.child = {}
        self.is_end = False
    
    def searchPrefix(self, tokens:list(str)):
        node = self
        for str in tokens:
            if not node.child[str]:
                return None
            node = node.child[str]
        return node

    def insert(self, tokens:list(str)):
        node = self
        for str in tokens:
            if not node.child[str]:
                node.child[str] = Trie()
            node = node.child[str]
        node.is_end = True
    
    def search(self, tokens:list(str)):
        node = self.searchPrefix(tokens)
        return node is not None and node.is_end
    
    def traverse_d_k(tokens:list(str)) -> str:
        '''
        Traverse by domain knowledge
        '''
        for knowledge in domain_knowledge:
            if knowledge in tokens:
                return knowledge
        return 'DEFAULT'
    
    def traverse_m_f(tokens:list(str)):
        '''
        Traverse by most frequent tokens'''
        pass

    def traverse_prefix(tokens:list(str)):
        '''
        Traverse by prefix tokens'''
        pass

    