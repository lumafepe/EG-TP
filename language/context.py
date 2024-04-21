from collections import Counter

class Context():
    def __init__(self,parent=None):
        self.symbols = {} if parent is None else parent.symbols.copy()
        self.used = Counter()

    def in_global_scope(self) -> None:
        return self.parent is None

    def used_symbols(self) -> None:
        return self.used
    
    def use_symbol(self,symbol) -> None:
        self.used[symbol]+=1
    
    def is_declared(self,symbol) -> None:
        return symbol in self.symbols
    
    #elem is the whole declaration, not just the value
    def declare_symbol(self,symbol,elem) -> None:
        self.symbols[symbol]=elem
