from abc import ABC, abstractmethod

from enum import Enum
from typing import Iterable

# class syntax

class IssueType(Enum):
    Info = 1
    Warning = 2
    Error = 3

class Issue:
    def __init__(self, type: IssueType, elem, msg: str) -> None:
        self.valueType = type
        self.elem = elem
        self.msg = msg
    def __str__(self) -> str:
        return self.msg
    def __repr__(self) -> str:
        return str(self)
    
class TypeError(Issue):
    def __init__(self, expression, expectedType, actualType) -> None:
        super().__init__(IssueType.Error, expression, f"TypeError: expected type '{expectedType}'; got '{actualType}'")

    @staticmethod
    def check(expression, expectedType, context) -> Iterable[TypeError]:
        if expectedType != None:
            actualType = expression.type(context)
            if actualType != None and not expectedType.isAssignableFrom(actualType):
                yield TypeError(expression, expectedType, actualType)