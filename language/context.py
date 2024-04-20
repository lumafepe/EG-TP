from abc import ABC, abstractmethod
from enum import Enum
from .types import Type

class Kind(Enum):
    Constant = 0
    Variable = 1
    Literal = 2

class Context():
    def __init__(self,parent=None):
        self.symbols = {} if parent is None else parent.symbols.copy()
        self.used = set()

    def in_global_scope(self) -> None:
        return self.parent is None

    def used_symbols(self) -> None:
        pass
    
    def use_symbol(self,symbol) -> None:
        self.used.add(symbol)
    
    def is_declared(self,symbol) -> None:
        return symbol in self.symbols
    
    #elem is the whole declaration, not just the value
    def declare_symbol(self,symbol,elem) -> None:
        self.symbols[symbol]=elem
