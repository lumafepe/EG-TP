from abc import ABC, abstractmethod
from .context import Context, Kind
from .issue import Issue, IssueType
from .types import Type,BOOL,INT,LIST,ARRAY,TUPLE,CHAR,STRING
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









"""

# class syntax

class Operation_Type(Enum):
    OR = '||'
    AND = '&&'
    EQUALITY = '=='
    INEQUALITY = '!='
    GT = '>'
    GTE = '>='
    LT = '<'
    LTE = '<='
    ADDITION = '+'
    SUBTRACTION = '-'
    MULTIPLICATION = '*'
    DIVISION = '/'
    MODULO = '%' 
    EXPONENTIATION = '^'
    BITWISE_NOT = '~'
    NOT = '!'
    HASHTAG = '#' #TODO Change
    INDEXATION = '#[]' #TODO Change
    ELEMENT = '##'

class Operation(Expression):
    is_element = re.compile(r"#\d+")
    
    def __init__(self,opType:str,exps:list[Element]):
        if re.match(self.is_element,opType):
            self.opType = Operation_Type('##')
            self.exps = exps
            self.exps.append(Const(int(opType[1:]),INT()))
        else:
            self.opType = Operation_Type(opType)
            self.exps = exps
    
    def __eq__(self, obj) -> bool:
        return self.__class__ == obj.__class__ and self.opType == obj.opType and len(self.exps)==len(obj.exps) and all(map(lambda x:x[0]==x[1],zip(self.exps,obj.exps)))
    
    def __str__(self):
        if len(self.exps)==1:
            return self.opType.value + ' ' + str(self.exps[0]) 
        else:
            match self.opType:
                case Operation_Type.INDEXATION:
                    return str(self.exps[0])+f'[{str(self.exps[1])}]'
                case _:
                    return str(self.exps[0]) + f' {self.opType.value} ' + str(self.exps[1])
                
    def validate(self, context) -> iter[Issue]:
        errors=[]
        for exp in self.exps:
            exp.validate(context)
        if len(self.exps)==1:
            pass
        else: #TODO
            pass
            
    
    def returnType(self) -> Type:
        match self.opType:
            case Operation_Type.OR:
                return BOOL()
            case Operation_Type.AND:
                return BOOL()
            case Operation_Type.EQUALITY:
                return BOOL()
            case Operation_Type.INEQUALITY:
                return BOOL()
            case Operation_Type.GT:
                return BOOL()
            case Operation_Type.GTE:
                return BOOL()
            case Operation_Type.LT:
                return BOOL()
            case Operation_Type.LTE:
                return BOOL()
            case Operation_Type.NOT:
                return BOOL()
            case Operation_Type.ADDITION:
                return self.exps[0].returnType()
            case Operation_Type.SUBTRACTION:
                return self.exps[0].returnType()
            case Operation_Type.MULTIPLICATION:
                return self.exps[0].returnType()
            case Operation_Type.DIVISION:
                return self.exps[0].returnType()
            case Operation_Type.MODULO:
                return self.exps[0].returnType()
            case Operation_Type.EXPONENTIATION:
                return self.exps[0].returnType()
            case Operation_Type.BITWISE_NOT:
                return self.exps[0].returnType()
            case Operation_Type.HASHTAG:
                return self.exps[0].returnType()
            case Operation_Type.INDEXATION: #TODO FIX THIS
                return self.exps[0].returnType()
            case Operation_Type.ELEMENT: #TODO FIX THIS
                typ = self.exps[0].returnType()
                if typ.__class__ == LIST().__class__ :
                    return typ.type
                elif typ.__class__ == ARRAY().__class__ :
                    return typ.type
                elif typ.__class__ == TUPLE().__class__:
                    return self.types[self.exps[1].value]

"""