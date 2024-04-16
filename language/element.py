from abc import ABC, abstractmethod
from .context import Context
from .issue import Issue
from typing import List


class Element(ABC):
    @abstractmethod
    def validate(self, context) -> List[Issue]:
        pass

    @abstractmethod
    def __eq__(self, obj) -> bool:
        pass
    
    @abstractmethod
    def __str__(self, obj) -> bool:
        pass