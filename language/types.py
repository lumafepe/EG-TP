from abc import ABC, abstractmethod
class Type(ABC):
    
    def isInstanceOf(self,value):
        return value.getType() == self
    
    @abstractmethod
    def __str__(self):
        pass
    
    def __repr__(self) -> str:
        return str(self)
    
    def __eq__(self,other):
        return self.__class__ == other.__class__

class INT(Type):
    def __str__(self):
        return 'INT'
    
class STRING(Type):
    def __str__(self):
        return 'STRING'

class CHAR(Type):
    def __str__(self):
        return 'CHAR'

class BOOL(Type):
    def __str__(self):
        return 'BOOL'

class TUPLE(Type):
    def __init__(self,types : list[Type]):
        self.types = types
    def __str__(self):
        return "Tuple ("+', '.join(str(t) for t in self.types)+')'
    def __eq__(self, other):
        return super().__eq__(other) and all(map(lambda x: x[0]==x[1],zip(self.types,other.types)))

class ARRAY(Type):
    def __init__(self,type):
        self.type = type
        
    def __str__(self):
        return f"Array [{str(self.type)}]"
    
    def __eq__(self, other):
        return super().__eq__(other) and self.type == other.type

class LIST(Type):
    def __init__(self,type):
        self.type = type
    def __str__(self):
        return f"List <{str(self.type)}>"
    def __eq__(self, other):
        return super().__eq__(other) and self.type == other.type