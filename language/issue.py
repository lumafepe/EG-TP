from abc import ABC, abstractmethod

from enum import Enum

# class syntax

class Issue(Enum):
    Warning = 1
    Error = 2
    Info = 3
