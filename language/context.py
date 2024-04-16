from abc import ABC, abstractmethod

class Type(ABC):
    
    @abstractmethod
    def isInstanceOf(self,type):
        pass
    
    @abstractmethod
    def __str__(self):
        pass
    
    @abstractmethod
    def __eq__(self,type):
        pass
    

class Context():
    def __init__(self,parent=None):
        self.symbols = {} if parent is None else parent.symbols.copy()
        self.used = set()

    def in_global_scope(self):
        return self.parent is None

    def used_symbols(self):
        pass
    
    def use_symbol(self,symbol):
        self.used.add(symbol)
    
    def is_declared(self,symbol):
        return symbol in self.symbols
    
    def declare_symbol(self,symbol,type):
        self.symbols[symbol]=type
