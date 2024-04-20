from abc import ABC, abstractmethod
from .context import Context, Kind
from .issue import Issue, IssueType
from .types import Type,BOOL,INT,LIST,ARRAY,TUPLE,CHAR,STRING,Container
from typing import List
from enum import Enum
import re

class Element(ABC):
    @abstractmethod
    def validate(self, context: Context) -> iter[Issue]:
        pass

    @abstractmethod
    def __eq__(self, obj) -> bool:
        pass
    
    @abstractmethod
    def __str__(self) -> str:
        pass

class Expression(Element):
    @abstractmethod
    def kind(self) -> Kind:
        pass

    @abstractmethod
    def type(self) -> Type:
        pass

class Value(Expression):
    def __init__(self,value,type:Type):
        assert type in [INT, BOOL, CHAR, STRING]
        self.value = value
        self.type = type

    def kind(self) -> Kind:
        return Kind.Constant
    
    def type(self) -> Type:
        return self.type

    def validate(self, context: Context) -> iter[Issue]:
        return []
    
    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) and self.type == obj.type and self.value == obj.value

    def __str__(self) -> str:
        return self.type.printInstance(self.value)


#Assumes all operands are of the same type, or are assignable to the same type
class Operation(Expression):
    def __init__(self, operator: str, operands: list[Expression], allowedTypes: list[Type]) -> None:
        self.operator = operator
        self.operands = operands
        self.allowedTypes = allowedTypes

    def kind(self) -> Kind:
        return Kind.Constant if all(o.kind() == Kind.Constant for o in self.operands) else Kind.Literal

    def validate(self, context: Context) -> iter[Issue]:
        for o in self.operands:
            yield from o.validate(context)
        
        bigger_type = self.operands[0].type()
        for o in self.operands:
            if not bigger_type.isAssignableFrom(o.type()):
                if o.type().isAssignableFrom(bigger_type):
                    bigger_type = o.type()
                else:
                    yield Issue(IssueType.Error, "TypeError. TODO: make cool messages")

    def __eq__(self, obj: object) -> bool:
        return type(self) == type(obj) \
            and self.operator == obj.operator \
            and self.operands == obj.operands

class UnaryOperation(Operation):
    def __init__(self, operator: str, suffixed: bool, operand: Expression, allowedTypes: list[Type]) -> None:
        super().__init__(operator, [operand], allowedTypes)
        self.suffixed = suffixed

    def operand(self):
        return self.operands[0]
    
    def __str__(self) -> bool:
        return f"{self.operand()}{self.operator}" if self.suffixed else f"{self.operator}{self.operand()}"


class BinaryOperation(Operation):
    def __init__(self, operator: str, lterm: Expression, rterm: Expression, allowedTypes: list[Type]) -> None:
        super().__init__(operator, [lterm, rterm], allowedTypes)

    def lterm(self):
        return self.operands[0]
    
    def rterm(self):
        return self.operands[1]

    def __str__(self) -> bool:
        return f"{self.lterm()} {self.operator} {self.rterm()}"




class ArrayIndex(Expression):
    def __init__(self, array: Expression, index: Expression) -> None:
        self.array = array
        self.index = index

    def kind(self) -> Kind:
        return Kind.Variable
    
    def type(self) -> Type:
        return self.array.type().contained
    
    def validate(self, context: Context) -> iter[Issue]:
        yield from self.array.validate()
        yield from self.index.validate()
        if type(self.array.type()) != ARRAY:
            yield Issue(IssueType.Error, self.array, "TypeError: TODO msg fixe")  
        if type(self.index.type()) != INT:
            yield Issue(IssueType.Error, self.index, "TypeError: TODO msg fixe")

    def __eq__(self, obj: object) -> bool:
        return type(self) == type(obj) and self.array == obj.array and self.index == obj.index
    
    def __str__(self) -> str:
        return f"{self.array}[{self.index}]"
    

class TupleIndex(Expression):
    def __init__(self, tuple: Expression, index: int) -> None:
        self.tuple = tuple
        self.index = index

    def kind(self) -> Kind:
        return Kind.Variable
    
    def type(self) -> Type:
        return self.tuple.type().tupled[self.index]

    def validate(self, context: Context) -> iter[Issue]:
        yield from self.tuple.validate()
        if type(self.tuple.type()) != TUPLE:
            yield Issue(IssueType.Error, self.tuple, "TypeError: TODO msg fixe")  

    def __eq__(self, obj: object) -> bool:
        return type(self) == type(obj) and self.tuple == obj.tuple and self.index == obj.index
    
    def __str__(self) -> str:
        return f"{self.tuple}#{self.index}"