from abc import ABC, abstractmethod
from .context import Context
from typing import List,Tuple

class Element(ABC):
    @abstractmethod
    def validate(self, context) -> Tuple[bool, List[str]]:
        pass

    @abstractmethod
    def __eq__(self, obj) -> bool:
        pass