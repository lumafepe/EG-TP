from abc import ABC, abstractmethod
from ..context import Context
from ..issue import Issue
from typing import Iterator

class Element(ABC):
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
    def toHTML(self, errors) -> str:
        pass