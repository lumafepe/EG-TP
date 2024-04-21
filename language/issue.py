from abc import ABC, abstractmethod

from enum import Enum

# class syntax

class IssueType(Enum):
    Warning = 1
    Error = 2
    Info = 3

class Issue:
    def __init__(self, type: IssueType, elem, msg: str) -> None:
        self.valueType = type
        self.elem = elem
        self.msg = msg
    def __str__(self) -> str:
        return self.msg
    def __repr__(self) -> str:
        return str(self)