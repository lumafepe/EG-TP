from abc import ABC, abstractmethod
from enum import Enum
from .element import Element
from ..context import Context
from typing import Iterator, Optional
from ..issue import Issue
class Type(Element):
    def __init__(self) -> None:
        super().__init__()
    
    #Determines whether an instance of a specified type can be assigned to a variable of the current type
    @abstractmethod
    def isAssignableFrom(self, other) -> bool:
        pass

    @abstractmethod
    def printInstance(self, value) -> str:
        pass
    
    @abstractmethod
    def toHTMLInstance(self, value) -> str:
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
    def __init__(self) -> None:
        super().__init__()
    def __eq__(self, other):
        return type(self) == type(other)
    
    def _toHTML(self, errors, depth=0) -> str:
        s = f"""<span class="type">{str(self)}</span>"""
        return s

class INT(Primitive):
    def __init__(self) -> None:
        super().__init__()
        
    def isAssignableFrom(self, other: Type) -> bool:
        return type(other) in [INT, CHAR, BOOL]
    
    def printInstance(self, value) -> str:
        return str(value)
    
    def toHTMLInstance(self, value) -> str:
        return f"""<span class="number">{str(value)}</span>"""

    def __str__(self):
        return 'int'
    
class STRING(Primitive):
    def __init__(self) -> None:
        super().__init__()
        
    def isAssignableFrom(self, other: Type) -> bool:
        return type(other) in [STRING]
    
    def printInstance(self, value) -> str:
        return f'"{value}"'
    
    def toHTMLInstance(self, value) -> str:
        return f"""<span class="text">"{value}"</span>"""

    def __str__(self):
        return 'string'

class CHAR(Primitive):
    def __init__(self) -> None:
        super().__init__()
        
    def isAssignableFrom(self, other: Type) -> bool:
        return type(other) in [CHAR]
    
    def printInstance(self, value) -> str:
        return f"'{value}'"
    
    def toHTMLInstance(self, value) -> str:
        return f"""<span class="text">'{value}'</span>"""
    
    def __str__(self):
        return 'char'

class BOOL(Primitive):
    def __init__(self) -> None:
        super().__init__()
        
    def isAssignableFrom(self, other: Type) -> bool:
        return type(other) in [BOOL]
    
    def printInstance(self, value) -> str:
        return "true" if value else "false"
    
    def toHTMLInstance(self, value) -> str:
        return f"""<span class="bool">{"true" if value else "false"}</span>"""

    def __str__(self):
        return 'bool'

class TUPLE(Type):
    def __init__(self, tupled: Optional[list[Type]]):
        super().__init__()
        assert tupled == None or len(tupled) >= 2
        self.tupled = tupled

    def isAssignableFrom(self, other: Type) -> bool:
        return isinstance(other, TUPLE) \
            and (self.tupled == None or (
                len(self.tupled) == len(other.tupled) \
                and all(a.isAssignableFrom(b) for a,b in zip(self.tupled,other.tupled)) \
            ))

    def printInstance(self, value) -> str:
        return f"({', '.join(t.printInstance(v) for t,v in zip(self.tupled, value))})"
    
    def toHTMLInstance(self, value) -> str:
        return f"""<span class="encloser">({'<span class="operator">, </span>'.join(t.toHTMLInstance(v) for t,v in zip(self.tupled, value))})</span>"""


    def __eq__(self, other):
        return type(self) == type(other) and self.tupled == other.tupled

    def __str__(self):
        return f"({', '.join(str(t) for t in self.tupled) if self.tupled != None else ','})"

    def _toHTML(self, errors, depth=0) -> str:
        return f"""<span class="encloser">({'<span class="operator">, </span>'.join(tip.toHTML(errors) for tip in self.tupled)})</span>"""


class Container(Type):
    def __init__(self, contained: Optional[Type]) -> None:
        super().__init__()
        self.contained = contained

    def isAssignableFrom(self, other: Type) -> bool:
        return type(self) == type(other) \
            and (self.contained == None or self.contained.isAssignableFrom(other.contained))

    def __eq__(self, other):
        return type(self) == type(other) and self.contained == other.contained

class ARRAY(Container):
    def __str__(self):
        return f"[{self.contained if self.contained != None else '?'}]"
    
    def printInstance(self, value) -> str:
        return f"[{', '.join(self.contained.printInstance(v) for v in value)}]"
    
    def toHTMLInstance(self, value) -> str:
        return f"""<span class="encloser">[{'<span class="operator">, </span>'.join(self.contained.toHTMLInstance(v) for v in value)}]</span>"""

    
    def _toHTML(self, errors, depth=0) -> str:
        return f"""<span class="encloser">[{self.contained.toHTML(errors)}]"""

class LIST(Container):
    def __str__(self):
        return f"<{self.contained if self.contained != None else '?'}>"
    
    def printInstance(self, value) -> str:
        return f"<{', '.join(self.contained.printInstance(v) for v in value)}>"
    
    def toHTMLInstance(self, value) -> str:
        return f"""<span class="encloser"><{'<span class="operator">, </span>'.join(self.contained.toHTMLInstance(v) for v in value)}></span>"""

    
    def _toHTML(self, errors, depth=0) -> str:
        return f"""<span class="encloser"><{self.contained.toHTML(errors)}>"""


class VOID(Type):
    def isAssignableFrom(self, other: Type) -> bool:
        return False

    def __str__(self):
        return "void"
    
    def __eq__(self, other: object):
        return type(self) == type(other)
    
    def _toHTML(self, errors, depth=0) -> str:
        assert False #This type shouldn't appear in html
    
    def printInstance(self, value) -> str:
        assert False #There are no void instances

    def toHTMLInstance(self, value) -> str:
        assert False #There are no void instances