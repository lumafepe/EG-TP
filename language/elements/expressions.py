from abc import ABC, abstractmethod
from typing import Iterator
from enum import Enum
from .types import Type,BOOL,INT,LIST,ARRAY,TUPLE,CHAR,STRING
from .element import Element
from ..context import Context
from ..issue import Issue, IssueType

class Kind(Enum):
    Constant = 0
    Variable = 1
    Literal = 2

class Expression(Element):
    @abstractmethod
    def kind(self) -> Kind:
        pass

    @abstractmethod
    def type(self,context : Context) -> Type:
        pass


class Value(Expression):
    def __init__(self,value,valueType:Type):
        assert type(valueType) in [INT, BOOL, CHAR, STRING]
        self.value = value
        self.type = valueType

    def kind(self) -> Kind:
        return Kind.Constant
    
    def type(self,context : Context) -> Type:
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
    def getBiggerType(self,context):
        bigger_type = self.values[0].type(context)
        for o in self.values:
            if not bigger_type.isAssignableFrom(o.type(context)):
                if o.type(context).isAssignableFrom(bigger_type):
                    bigger_type = o.type(context)
        return bigger_type

class Tuple(MultiValueExpression):
    def __init__(self, values: list[Expression]) -> None:
        super().__init__(values, '(' , ')')

    def validate(self, context: Context) -> Iterator[Issue]:
        yield from super().validate(context)
        if len(self.values) :
            yield Issue(IssueType.Error,self, "TypeError. TODO: make cool messages")
        

    def type(self,context : Context) -> Type:
        return TUPLE([t.type(context) for t in self.values])

class Array(UniTypeMultiValueExpression):
    def __init__(self, values: list[Expression]) -> None:
        super().__init__(values, '[' , ']')

    def validate(self, context: Context) -> Iterator[Issue]:
        yield from super().validate(context)
        bigger_type = self.values[0].type(context)
        for o in self.values:
            if not bigger_type.isAssignableFrom(o.type(context)):
                if o.type(context).isAssignableFrom(bigger_type):
                    bigger_type = o.type(context)
                else:
                    yield Issue(IssueType.Error,self, "TypeError. TODO: make cool messages")

    def type(self,context : Context) -> Type:
        return ARRAY(self.getBiggerType(context))
    
class List(UniTypeMultiValueExpression):
    def __init__(self, values: list[Expression]) -> None:
        super().__init__(values, '<' , '>')

    def validate(self, context: Context) -> Iterator[Issue]:
        yield from super().validate(context)
        bigger_type = self.values[0].type(context)
        for o in self.values:
            if not bigger_type.isAssignableFrom(o.type(context)):
                if o.type(context).isAssignableFrom(bigger_type):
                    bigger_type = o.type(context)
                else:
                    yield Issue(IssueType.Error,self,"TypeError. TODO: make cool messages")

    def type(self,context : Context) -> Type:
        return LIST(self.getBiggerType(context))


class Variable(Expression):
    
    def __init__(self,symbol) -> None:
        self.symbol = symbol
        
    def kind(self):
        return Kind.Variable
    
    def __eq__(self, obj: object) -> bool:
        return type(self)== type(obj) and self.symbol == obj.symbol

    def validate(self, context: Context) -> Iterator[Issue]:
        if not context.is_declared(self.symbol):
            yield Issue(IssueType.Error,self, "TypeError. Undefined Variable")
        context.use_symbol(self.symbol)
    
    def type(self, context: Context) -> Type:
        return context.get_variable_declaration(self.symbol).type()
        
    def __str__(self):
        return self.symbol
    
class Function_call(Expression):
    def __init__(self,name,args) -> None:
        self.name = name
        self.args = args
        
    def kind(self):
        return Kind.Literal
    
    def __eq__(self, obj: object) -> bool:
        return type(self)== type(obj) and self.name == obj.name and len(self.args) == len(obj.args) and all(t==k for t,k in zip(self.args,obj.args))

    def validate(self, context: Context) -> Iterator[Issue]:
        for o in self.args:
            yield from o.validate(context)
        if not context.is_declared(self.name):
            yield Issue(IssueType.Error,self, "TypeError. Undefined Funtion")
        context.use_symbol(self.name)
        
    def __str__(self):
        return self.name +'('+' ,'.join(str(t) for t in self.args) +')'
    
    def type(self, context: Context) -> Type:
        return context.get_funtion_declaration(self.symbol).type()


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
        
        bigger_type = self.operands[0].type(context)
        for o in self.operands:
            if not bigger_type.isAssignableFrom(o.type(context)):
                if o.type(context).isAssignableFrom(bigger_type):
                    bigger_type = o.type(context)
                else:
                    yield Issue(IssueType.Error,self, "TypeError. TODO: make cool messages")

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
    def type(self,context : Context) -> Type:
        return BOOL()

class Or(BooleanBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('||', lterm, rterm, [BOOL])
class And(BooleanBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('&&', lterm, rterm, [BOOL])

class Equality(BooleanBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression,) -> None:
        super().__init__('==', lterm, rterm, [INT,STRING,CHAR,BOOL,TUPLE,ARRAY,LIST])

class Inequality(BooleanBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression,) -> None:
        super().__init__('==', lterm, rterm, [INT,STRING,CHAR,BOOL,TUPLE,ARRAY,LIST])

class Gt(BooleanBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('>', lterm, rterm, [CHAR,INT])
class Gte(BooleanBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('>=', lterm, rterm, [CHAR,INT])
class Lt(BooleanBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('<', lterm, rterm, [CHAR,INT])
class Lte(BooleanBinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('<=', lterm, rterm, [CHAR,INT])

class NumericBinaryOperation(BinaryOperation):
    def __init__(self, operator: str, lterm: Expression, rterm: Expression) -> None:
        super().__init__(operator, lterm, rterm, [INT,CHAR])
        
    def type(self,context : Context) -> Type:
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
        super().__init__('~', operand,[INT,CHAR])
    def type(self,context : Context) -> Type:
        return self.operand.type(context)

class Not(UnaryOperation):
    def __init__(self, operand: Expression) -> None:
        super().__init__('!', operand,[BOOL])
    def type(self,context : Context) -> Type:
        return BOOL()

class Length(BinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('#', lterm, rterm, [ARRAY])
    def type(self,context : Context) -> Type:
        return INT()

class ArrayIndex(Expression):
    def __init__(self, array: Expression, index: Expression) -> None:
        self.array = array
        self.index = index

    def kind(self) -> Kind:
        if self.array.kind() == Kind.Constant and self.index.kind() == Kind.Constant:
            return Kind.Constant

        if self.array.kind() == Kind.Variable:
            return Kind.Variable

        return Kind.Literal
    
    def type(self,context : Context) -> Type:
        return self.array.type(context).contained
    
    def validate(self, context: Context) -> Iterator[Issue]:
        yield from self.array.validate()
        yield from self.index.validate()
        if type(self.array.type(context)) != ARRAY:
            yield Issue(IssueType.Error, self.array, "TypeError: TODO msg fixe")  
        if type(self.index.type(context)) != INT:
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
        return self.tuple.kind()
    
    def type(self,context : Context) -> Type:
        return self.tuple.type(context).tupled[self.index]

    def validate(self, context: Context) -> Iterator[Issue]:
        yield from self.tuple.validate()
        if type(self.tuple.type(context)) != TUPLE:
            yield Issue(IssueType.Error, self.tuple, "TypeError: TODO msg fixe")  

    def __eq__(self, obj: object) -> bool:
        return type(self) == type(obj) and self.tuple == obj.tuple and self.index == obj.index
    
    def __str__(self) -> str:
        return f"{self.tuple}#{self.index}"