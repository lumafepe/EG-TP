from abc import ABC, abstractmethod
from enum import Enum
from .element import Element
from ..context import Context
from typing import Iterator
from ..issue import Issue
class Type(Element):
    #Determines whether an instance of a specified type can be assigned to a variable of the current type
    @abstractmethod
    def isAssignableFrom(self, other) -> bool:
        pass

    @abstractmethod
    def printInstance(self, value) -> str:
        pass

    @abstractmethod
    def __eq__(self, other: object):
        pass

    @abstractmethod
    def __str__(self):
        pass
    
    def __repr__(self) -> str:
        return str(self)
    
    def validate(self, context: Context) -> Iterator[Issue]:
        return [] #TODO
     

class Primitive(Type):
    def __eq__(self, other):
        return type(self) == type(other)

class INT(Primitive):
    def isAssignableFrom(self, other: Type) -> bool:
        return type(other) in [INT, CHAR, BOOL]
    
    def printInstance(self, value) -> str:
        return str(value)

    def __str__(self):
        return 'int'
    
class STRING(Primitive):
    def isAssignableFrom(self, other: Type) -> bool:
        return type(other) in [STRING]
    
    def printInstance(self, value) -> str:
        return f'"{value}"'

    def __str__(self):
        return 'string'

class CHAR(Primitive):
    def isAssignableFrom(self, other: Type) -> bool:
        return type(other) in [CHAR]
    
    def printInstance(self, value) -> str:
        return f"'{value}'"
    
    def __str__(self):
        return 'char'

class BOOL(Primitive):
    def isAssignableFrom(self, other: Type) -> bool:
        return type(other) in [BOOL]
    
    def printInstance(self, value) -> str:
        return "true" if value else "false"

    def __str__(self):
        return 'bool'

class TUPLE(Type):
    def __init__(self, tupled: list[Type]):
        assert len(tupled) >= 2
        self.tupled = tupled

    def isAssignableFrom(self, other: Type) -> bool:
        return isinstance(other, TUPLE) \
            and len(self.tupled) == len(other.tupled) \
            and all(a.isAssignableFrom(b) for a,b in zip(self.tupled,other.tupled))

    def printInstance(self, value) -> str:
        return f"({', '.join(t.printInstance(v) for t,v in zip(self.tupled, value))})"

    def __eq__(self, other):
        return type(self) == type(other) and self.tupled == other.tupled

    def __str__(self):
        return f"({', '.join(self.tupled)})"

class Container(Type):
    def __init__(self, contained: Type) -> None:
        self.contained = contained

    def isAssignableFrom(self, other: Type) -> bool:
        return type(self) == type(other) \
            and self.contained.isAssignableFrom(other.contained)

    def __eq__(self, other):
        return type(self) == type(other) and self.contained == other.contained

class ARRAY(Container):
    def __str__(self):
        return f"[{self.contained}]"
    
    def printInstance(self, value) -> str:
        return f"[{', '.join(self.contained.printInstance(v) for v in value)}]"

class LIST(Container):
    def __str__(self):
        return f"<{self.contained}>"
    
    def printInstance(self, value) -> str:
        return f"<{', '.join(self.contained.printInstance(v) for v in value)}>"