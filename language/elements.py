from abc import ABC, abstractmethod
from .context import Context, Kind
from .issue import Issue, IssueType
from .types import Type,BOOL,INT,LIST,ARRAY,TUPLE,CHAR,STRING
from typing import Iterator
from enum import Enum
import re

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

class Expression(Element):
    @abstractmethod
    def kind(self) -> Kind:
        pass

    @abstractmethod
    def type(self) -> Type:
        pass

class Value(Expression):
    def __init__(self,value,valueType:Type):
        assert type(valueType) in [INT, BOOL, CHAR, STRING]
        self.value = value
        self.type = valueType

    def kind(self) -> Kind:
        return Kind.Constant
    
    def type(self) -> Type:
        return self.type

    def validate(self, context: Context) -> Iterator[Issue]:
        return []
    
    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) and self.type == obj.type and self.value == obj.value

    def __str__(self) -> str:
        return self.type.printInstance(self.value)
    
    
class MultiValueExpression(Expression):
    def __init__(self, values: list[Expression],stringOpener:str,stringCloser:str) -> None:
        self.values = values
        self.stringOpener = stringOpener
        self.stringCloser = stringCloser
    
    def __str__(self) -> str:
        return self.stringOpener+', '.join(str(s) for s in self.values) + self.stringCloser
    
    def __eq__(self, obj: object) -> bool:
        return type(self) == type(obj) and len(self.values) == len(obj.values) and all(a==b for a,b in zip(self.values,obj.values))

    def kind(self) -> Kind:
        if all(t.kind() == Kind.Constant for t in self.values):
            return Kind.Constant
        else:
            return Kind.Literal
        
    def validate(self, context: Context) -> Iterator[Issue]:
        for o in self.values:
            yield from o.validate(context)


class UniTypeMultiValueExpression(MultiValueExpression):
    def getBiggerType(self):
        bigger_type = self.values[0].type()
        for o in self.values:
            if not bigger_type.isAssignableFrom(o.type()):
                if o.type().isAssignableFrom(bigger_type):
                    bigger_type = o.type()
        return bigger_type

class Tuple(MultiValueExpression):
    def __init__(self, values: list[Expression], stringOpener: str, stringCloser: str) -> None:
        super().__init__(values, '(' , ')')

    def validate(self, context: Context) -> Iterator[Issue]:
        yield from super().validate(context)
        if len(self.values) :
            yield Issue(IssueType.Error,self, "TypeError. TODO: make cool messages")
        

    def type(self) -> Type:
        return TUPLE([t.type() for t in self.values])

class Array(UniTypeMultiValueExpression):
    def __init__(self, values: list[Expression], stringOpener: str, stringCloser: str) -> None:
        super().__init__(values, '[' , ']')

    def validate(self, context: Context) -> Iterator[Issue]:
        yield from super().validate(context)
        bigger_type = self.values[0].type()
        for o in self.values:
            if not bigger_type.isAssignableFrom(o.type()):
                if o.type().isAssignableFrom(bigger_type):
                    bigger_type = o.type()
                else:
                    yield Issue(IssueType.Error,self, "TypeError. TODO: make cool messages")

    def type(self) -> Type:
        return ARRAY(self.getBiggerType())
    
class List(UniTypeMultiValueExpression):
    def __init__(self, values: list[Expression], stringOpener: str, stringCloser: str) -> None:
        super().__init__(values, '<' , '>')

    def validate(self, context: Context) -> Iterator[Issue]:
        yield from super().validate(context)
        bigger_type = self.values[0].type()
        for o in self.values:
            if not bigger_type.isAssignableFrom(o.type()):
                if o.type().isAssignableFrom(bigger_type):
                    bigger_type = o.type()
                else:
                    yield Issue(IssueType.Error,self,"TypeError. TODO: make cool messages")

    def type(self) -> Type:
        return LIST(self.getBiggerType())




#Assumes all operands are of the same type, or are assignable to the same type
class Operation(Expression):
    def __init__(self, operator: str, operands: list[Expression], allowedTypes: list[Type]) -> None:
        self.operator = operator
        self.operands = operands
        self.allowedTypes = allowedTypes

    def kind(self) -> Kind:
        return Kind.Constant if all(o.kind() == Kind.Constant for o in self.operands) else Kind.Literal

    def validate(self, context: Context) -> Iterator[Issue]:
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
    def __init__(self, operator: str, operand: Expression, allowedTypes: list[Type]) -> None:
        super().__init__(operator, [operand], allowedTypes)

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

class BooleanBinaryOperation(BinaryOperation):
    def type(self) -> Type:
        return BOOL()

class Or(BooleanBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('||', lterm, rterm, [BOOL()])
class And(BooleanBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('&&', lterm, rterm, [BOOL()])

class Equality(BooleanBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression,) -> None:
        super().__init__('==', lterm, rterm, [INT(),STRING(),CHAR(),BOOL(),TUPLE(),ARRAY(),LIST()])

class Inequality(BooleanBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression,) -> None:
        super().__init__('==', lterm, rterm, [INT(),STRING(),CHAR(),BOOL(),TUPLE(),ARRAY(),LIST()])

class Gt(BooleanBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('>', lterm, rterm, [CHAR(),INT()])
class Gte(BooleanBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('>=', lterm, rterm, [CHAR(),INT()])
class Lt(BooleanBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('<', lterm, rterm, [CHAR(),INT()])
class Lte(BooleanBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('<=', lterm, rterm, [CHAR(),INT()])

class NumericBinaryOperation(BinaryOperation):
    def __init__(self, operator: str, lterm: Expression, rterm: Expression) -> None:
        super().__init__(operator, lterm, rterm, [INT(),CHAR()])
        
    def type(self) -> Type:
        if self.lterm.type == CHAR() and self.rterm.type == CHAR():
            return CHAR()
        else:
            return INT()

class Addition(NumericBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('+', lterm, rterm)

class Subtraction(NumericBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('-', lterm, rterm)

class Multiplication(NumericBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('*', lterm, rterm)

class Division(NumericBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('/', lterm, rterm)

class Modulo(NumericBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('%', lterm, rterm)

class Expotentiation(NumericBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('^', lterm, rterm)


class BitwiseNot(UnaryOperation):
    def __init__(self, operand: Expression) -> None:
        super().__init__('~', operand,[INT(),CHAR()])
    def type(self) -> Type:
        return self.operand.type()

class Not(UnaryOperation):
    def __init__(self, operand: Expression) -> None:
        super().__init__('!', operand,[BOOL()])
    def type(self) -> Type:
        return BOOL()

class Length(BinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('#', lterm, rterm, [ARRAY()])
    def type(self) -> Type:
        return INT()
