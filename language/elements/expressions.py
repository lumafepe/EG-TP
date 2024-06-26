from abc import ABC, abstractmethod
from typing import Iterator, Optional
from enum import Enum
from .types import Type,BOOL,INT,LIST,ARRAY,TUPLE,CHAR,STRING
from .element import Element
from ..context import Context
from ..issue import Issue, IssueType, TypeError
import pygraphviz as pgv

class Kind(Enum):
    Constant = 0
    Variable = 1
    Literal = 2

class Expression(Element):
    def __init__(self) -> None:
        super().__init__()
    @abstractmethod
    def kind(self, context: Context) -> Optional[Kind]:
        pass

    @abstractmethod
    def type(self, context: Context) -> Optional[Type]:
        pass


class Value(Expression):
    def __init__(self,value,valueType:Type):
        super().__init__()
        assert type(valueType) in [INT, BOOL, CHAR, STRING]
        self.value = value
        self.valueType = valueType

    def kind(self, context: Context) -> Optional[Kind]:
        return Kind.Constant
    
    def type(self, context: Context) -> Optional[Type]:
        return self.valueType

    def validate(self, context: Context) -> Iterator[Issue]:
        return []
    
    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) \
            and self.valueType == obj.valueType \
                and self.value == obj.value
                
    
    def __str__(self) -> str:
        return self.valueType.printInstance(self.value)
    
    def _toHTML(self, errors, depth=0) -> str:
        return self.valueType.toHTMLInstance(self.value)
    
    
class MultiValueExpression(Expression):
    def __init__(self, values: list[Expression],stringOpener:str,stringCloser:str) -> None:
        super().__init__()
        self.values = values
        self.stringOpener = stringOpener
        self.stringCloser = stringCloser
    
    def __str__(self) -> str:
        return self.stringOpener+', '.join(str(s) for s in self.values) + self.stringCloser
    
    def _toHTML(self, errors, depth=0) -> str:
        return f"""<span class="encloser">{self.stringOpener}{'<span class="operator">, </span>'.join(s.toHTML(errors) for s in self.values)}{self.stringCloser}</span>"""
        
    
    def __eq__(self, obj: object) -> bool:
        return type(self) == type(obj) \
            and self.stringOpener == obj.stringOpener \
            and self.stringCloser == obj.stringCloser \
            and len(self.values) == len(obj.values) \
            and all(a==b for a,b in zip(self.values,obj.values))
            
    def kind(self, context: Context) -> Optional[Kind]:
        if all(t.kind(context) == Kind.Constant for t in self.values):
            return Kind.Constant
        else:
            return Kind.Literal
        
    def validate(self, context: Context) -> Iterator[Issue]:
        for o in self.values:
            yield from o.validate(context)


class UniTypeMultiValueExpression(MultiValueExpression):
    def getBiggerType(self,context):
        bigger_type = self.values[0].type(context)
        for v in self.values:
            vType = v.type(context)
            if bigger_type == None:
                bigger_type = vType
            elif vType != None and not bigger_type.isAssignableFrom(vType) and vType.isAssignableFrom(bigger_type):
                bigger_type = vType
        return bigger_type
    
    def validate(self, context: Context) -> Iterator[Issue]:
        yield from super().validate(context)
        bigger_type = self.getBiggerType(context)
        for o in self.values:
            yield from TypeError.check(o, bigger_type, context)

class Tuple(MultiValueExpression):
    def __init__(self, values: list[Expression]) -> None:
        super().__init__(values, '(' , ')')

    def validate(self, context: Context) -> Iterator[Issue]:
        yield from super().validate(context)
        if len(self.values) < 2:
            yield Issue(IssueType.Error,self, "Tuples with less than two elements aren't allowed")
        

    def type(self, context: Context) -> Optional[Type]:
        return TUPLE([t.type(context) for t in self.values])

class Array(UniTypeMultiValueExpression):
    def __init__(self, values: list[Expression]) -> None:
        super().__init__(values, '[' , ']')

    def type(self, context: Context) -> Optional[Type]:
        return ARRAY(self.getBiggerType(context))
    
class NewArray(Expression):
    def __init__(self, elemType: Type, numElems: Expression) -> None:
        super().__init__()
        self.elemType = elemType
        self.numElems = numElems

    def kind(self, context: Context) -> Optional[Kind]:
        return Kind.Constant if self.numElems.kind(context) == Kind.Constant else Kind.Literal

    def type(self, context: Context) -> Optional[Type]:
        return ARRAY(self.elemType)

    def validate(self, context: Context) -> Iterator[Issue]:
        yield from self.elemType.validate(context)
        yield from self.numElems.validate(context)
        yield from TypeError.check(self.numElems, INT(), context)

    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) \
            and self.elemType == obj.elemType \
            and self.numElems == obj.numElems


    def __str__(self) -> str:
        return f"{self.elemType}[{self.numElems}]"

    def _toHTML(self, errors, depth=0) -> str:
        s = self.elemType.toHTML(errors)
        s += """<span class="operator">[</span>"""
        s += self.numElems.toHTML(errors)
        s += """<span class="operator">]</span>"""
        return s

class List(UniTypeMultiValueExpression):
    def __init__(self, values: list[Expression]) -> None:
        super().__init__(values, '<' , '>')

    def type(self, context: Context) -> Optional[Type]:
        return LIST(self.getBiggerType(context))


class Variable(Expression):
    
    def __init__(self,symbol) -> None:
        super().__init__()
        self.symbol = symbol
        
    def kind(self, context: Context) -> Optional[Kind]:
        if not context.is_declared_variable(self.symbol):
            return None
        
        declaration = context.get_variable_declaration(self.symbol)
        if declaration.const and declaration.value.kind(context) == Kind.Constant:
            return Kind.Constant

        return Kind.Variable
    
    def __eq__(self, obj: object) -> bool:
        return type(self)== type(obj) \
            and self.symbol == obj.symbol

    def validate(self, context: Context) -> Iterator[Issue]:
        if not context.is_declared(self.symbol):
            yield Issue(IssueType.Error,self, "Undefined Variable")
        context.use_symbol(self.symbol)
    
    def type(self, context: Context) -> Optional[Type]:
        if context.is_declared_variable(self.symbol):
            return context.get_variable_declaration(self.symbol).type(context)
        else:
            return None
        
    def __str__(self):
        return self.symbol
    
    def _toHTML(self, errors, depth=0) -> str:
        return f"""<span class="variable">{self.symbol}</span>"""
    
    
class Function_call(Expression):
    def __init__(self,name : str,args : list[Expression]) -> None:
        super().__init__()
        self.name = name
        self.args = args
        
    def kind(self, context: Context) -> Optional[Kind]:
        return Kind.Literal
    
    def __eq__(self, obj: object) -> bool:
        return type(self)== type(obj) \
            and self.name == obj.name \
            and len(self.args) == len(obj.args) \
            and all(t==k for t,k in zip(self.args,obj.args))
    
    def validate(self, context: Context) -> Iterator[Issue]:
        for o in self.args:
            yield from o.validate(context)
        if not context.is_declared_function(self.name):
            yield Issue(IssueType.Error,self, "Undefined Function")
        else:
            args = context.get_funtion_declaration(self.name).args
            elementTypes = [arg.type for arg in args]
            if len(args) != len(self.args):
                yield Issue(IssueType.Error,self, f"Wrong Number of arguments,  {len(args)} expected but {len(self.args)} where given")
            else:
                for arg,expectedType in zip(self.args,elementTypes):
                    if not expectedType.isAssignableFrom(arg.type(context)):
                        yield Issue(IssueType.Error,arg, f"Argument has wrong type. {str(expectedType)} expected but got {str(arg.type(context))} instead")
            
        context.use_symbol(self.name)
        
    def __str__(self) -> str :
        return self.name +'('+' ,'.join(str(t) for t in self.args) +')'
    
    def _toHTML(self, errors, depth=0) -> str:
        args = f"""<span class="encloser">({'<span class="operator">, </span>'.join(t.toHTML(errors) for t in self.args)})</span>"""
        return f"""<span class="line" index={depth}></span><span class="function">{self.name}{args}</span>"""
        
    
    def type(self, context: Context) -> Optional[Type]:
        return context.get_funtion_declaration(self.name).returnType
    
    def append_to_graph(self, graph: pgv.AGraph,NewScope=False, end=None):
        graph.add_node(str(self.id), label=str(self), shape="oval")
        return str(self.id),[(str(self.id),"")]


#Assumes all operands are of the same type, or are assignable to the same type
class Operation(Expression):
    def __init__(self, operator: str, operands: list[Expression], allowedTypes: list[type]) -> None:
        super().__init__()
        self.operator = operator
        self.operands = operands
        self.allowedTypes = allowedTypes
        for t in allowedTypes:
            assert issubclass(t, Type)

    def kind(self, context: Context) -> Optional[Kind]:
        return Kind.Constant if all(o.kind(context) == Kind.Constant for o in self.operands) else Kind.Literal

    def getBiggerType(self,context):
        bigger_type = self.operands[0].type(context)
        for o in self.operands:
            oType = o.type(context)
            if bigger_type == None:
                bigger_type = oType
            elif oType != None and not bigger_type.isAssignableFrom(oType) and oType.isAssignableFrom(bigger_type):
                bigger_type = oType
        return bigger_type

    def validate(self, context: Context) -> Iterator[Issue]:
        for o in self.operands:
            yield from o.validate(context)

        allAllowed = True
        for o in self.operands:
            oType = o.type(context)
            if oType != None and all(not isinstance(oType, t) for t in self.allowedTypes):
                yield Issue(IssueType.Error, o, f"Invalid operand of type {oType} for operator {self.operator}")
                allAllowed = False
        
        if allAllowed:
            for o in self.operands:
                yield from TypeError.check(o, self.getBiggerType(context), context)

    def __eq__(self, obj: object) -> bool:
        return type(self) == type(obj) \
            and self.operator == obj.operator \
            and all(t==k for t,k in zip(self.operands,obj.operands))


class UnaryOperation(Operation):
    def __init__(self, operator: str, operand: Expression, allowedTypes: list[type]) -> None:
        super().__init__(operator, [operand], allowedTypes)

    def operand(self):
        return self.operands[0]
    
    def __str__(self) -> bool:
        return f"{self.operator}{str(self.operand())}"
    
    def _toHTML(self, errors, depth=0) -> str:
        s =  f"""<span class="operator">{self.operator}</span>"""
        s += self.operand().toHTML(errors)
        return s


class BinaryOperation(Operation):
    def __init__(self, operator: str, lterm: Expression, rterm: Expression, allowedTypes: list[type]) -> None:
        super().__init__(operator, [lterm, rterm], allowedTypes)

    def lterm(self):
        return self.operands[0]
    
    def rterm(self):
        return self.operands[1]

    def __str__(self) -> bool:
        return f"{str(self.lterm())} {self.operator} {str(self.rterm())}"
    
    def _toHTML(self, errors, depth=0) -> str:
        s = self.lterm().toHTML(errors)
        s +=  f"""<span class="operator">{self.operator}</span>"""
        s += self.rterm().toHTML(errors)
        return s

class BooleanBinaryOperation(BinaryOperation):
    def type(self, context: Context) -> Optional[Type]:
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
        
    def type(self, context: Context) -> Optional[Type]:
        return self.getBiggerType(context)

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
    def type(self, context: Context) -> Optional[Type]:
        return self.operand.type(context)

class Not(UnaryOperation):
    def __init__(self, operand: Expression) -> None:
        super().__init__('!', operand,[BOOL])
    def type(self, context: Context) -> Optional[Type]:
        return BOOL()

class Length(BinaryOperation):
    def __init__(self, lterm: Expression, rterm: Expression) -> None:
        super().__init__('#', lterm, rterm, [ARRAY])
    def type(self, context: Context) -> Optional[Type]:
        return INT()

class ArrayIndex(Expression):
    def __init__(self, array: Expression, index: Expression) -> None:
        super().__init__()
        self.array = array
        self.index = index

    def kind(self, context: Context) -> Optional[Kind]:
        if self.array.kind(context) == Kind.Constant and self.index.kind(context) == Kind.Constant:
            return Kind.Constant

        if self.array.kind(context) == Kind.Variable:
            return Kind.Variable

        return Kind.Literal
    
    def type(self, context: Context) -> Optional[Type]:
        containerType = self.array.type(context)
        if isinstance(containerType, ARRAY):
            return containerType.contained
        else:
            return None
    
    def validate(self, context: Context) -> Iterator[Issue]:
        yield from self.array.validate(context)
        yield from self.index.validate(context)
        yield from TypeError.check(self.array, ARRAY(None), context)
        yield from TypeError.check(self.index, INT(), context)

    def __eq__(self, obj: object) -> bool:
        return type(self) == type(obj) \
            and self.array == obj.array \
            and self.index == obj.index

    
    def __str__(self) -> str:
        return f"{self.array}[{self.index}]"

    def _toHTML(self, errors, depth=0) -> str:
        s = self.array.toHTML(errors)
        s += """<span class="operator">[</span>"""
        s += self.index.toHTML(errors)
        s += """<span class="operator">]</span>"""
        return s

class TupleIndex(Expression):
    def __init__(self, tuple: Expression, index: int) -> None:
        super().__init__()
        self.tuple = tuple
        self.index = index

    def kind(self, context: Context) -> Optional[Kind]:
        return self.tuple.kind(context)
    
    def type(self, context: Context) -> Optional[Type]:
        containerType = self.tuple.type(context)
        if isinstance(containerType, TUPLE) and self.index < len(containerType.tupled):
            return self.tuple.type(context).tupled[self.index]
        else:
            return None

    def validate(self, context: Context) -> Iterator[Issue]:
        yield from self.tuple.validate(context)
        
        ttype = self.tuple.type(context)
        if not isinstance(ttype, TUPLE):
            yield TypeError(self.tuple, TUPLE(None), ttype)
        elif self.index >= len(self.tuple.type(context).tupled):
            yield Issue(IssueType.Error, self, "Tuple index is out of bounds")

    def __eq__(self, obj: object) -> bool:
        return type(self) == type(obj) \
            and self.tuple == obj.tuple \
            and self.index == obj.index
    
    def __str__(self) -> str:
        return f"{self.tuple}#{self.index}"
    
    def _toHTML(self, errors, depth=0) -> str:
        s = self.tuple.toHTML(errors)
        s += f"""<span class="operator">#{self.index}</span>"""
        return s