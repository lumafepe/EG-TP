from abc import ABC, abstractmethod
from .context import Context
from .issue import Issue
from .types import Type,BOOL,INT
from typing import List
from enum import Enum
import re

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
    @abstractmethod
    def returnType(self) -> Type:
        pass

class Const(Element):
    def __init__(self,value,type:Type):
        self.value = value
        self.type = type
        
    def validate(self, context) -> List[Issue]:
        pass
        
    def __eq__(self, obj) -> bool:
        return self.__class__ == obj.__class__ and self.type == obj.type and self.value == obj.value
        
    def returnType(self) -> Type:
        return self.type
    
    def __str__(self) -> str:
        return str(self.type) + str(self.value)


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

class Operation(Element):
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
                
    def validate(self, context) -> List[Issue]:
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

