from abc import ABC, abstractmethod
from ..context import Context
from ..issue import Issue,IssueType
from typing import Iterator

class Element(ABC):
    last_id = 0
    
    def __init__(self) -> None:
        Element.last_id += 1
        self.id = Element.last_id

    @abstractmethod
    def validate(self, context: Context) -> Iterator[Issue]:
        pass

    @abstractmethod
    def __eq__(self, obj) -> bool:
        pass
    
    @abstractmethod
    def __str__(self) -> str:
        pass
    
    def __repr__(self) -> str:
        return str(self)
    
    @abstractmethod
    def __hash__(self):
        pass
    
    @abstractmethod
    def _toHTML(self, errors, depth=0) -> str:
        pass
    
    def toHTML(self,errors, depth=0) -> str :
        if self.id in errors:
            objErrors = errors[self.id]
            
            for typ,clas in [(IssueType.Error,"error"),(IssueType.Warning,"warning"),(IssueType.Info,"sugestion")]:
                for error in objErrors:
                    if error.valueType == typ:
                        return f"""<span class="{clas}" message="{error.msg}">{self._toHTML(errors,depth)}</span>"""
        else: return self._toHTML(errors,depth)
        
