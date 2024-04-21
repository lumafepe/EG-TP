from typing import Iterator, Optional
from .element import Element
from .expressions import Expression, Kind
from .types import Type
from ..context import Context
from ..issue import Issue, IssueType


class Declaration(Element):
    def __init__(self, const: bool, variable: str, type: Optional[Type], value: Optional[Expression]) -> None:
        self.const = const
        self.variable = variable
        self.valueType = type
        self.value = value

    def type(self, context: Context):
        return self.valueType if self.valueType != None else self.value.type(context)

    def validate(self, context: Context) -> Iterator[Issue]:
        if self.valueType != None:
            yield from self.valueType.validate(context)

        if self.value != None:
            yield from self.value.validate(context)
        
        if self.value == None:
            if self.const:
                yield Issue(IssueType.Error, self, "Constants must be initialized")
            elif self.valueType == None:
                yield Issue(IssueType.Error, self, "Cannot infer type of uninitialized variable")
        else:
            yield from TypeError.check(self.value, self.valueType, context)

        if context.is_declared(self.variable):
            yield Issue(IssueType.Error, self, "Symbol already declared")
        else:
            context.declare_variable(self)

    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) \
            and self.const == obj.const \
            and self.variable == obj.variable \
            and self.valueType == obj.type \
            and self.value == obj.value
    
    def __str__(self) -> str:
        return f"{'const' if self.const else 'var'} {self.variable}{f': {self.valueType}' if self.valueType != None else ''}{f' = {self.value}' if self.value !=None else ''}"
    

class Assignment(Element):
    def __init__(self, dest: Expression, value: Expression) -> None:
        self.dest = dest
        self.value = value

    def validate(self, context: Context) -> Iterator[Issue]:
        yield from self.dest.validate(context)
        yield from self.value.validate(context)

        if self.dest.kind() != Kind.Variable:
            yield Issue(IssueType.Error, self, f"Cannot assign to expression of kind {self.dest.kind()}")
        else:
            yield from TypeError.check(self.value, self.dest.type(context), context)

    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) and self.dest == obj.dest and self.value == obj.value

    def __str__(self) -> str:
        return f"{self.dest} = {self.value}"


class Program(Element):
    def __init__(self, instructions: list[Element]) -> None:
        self.instructions = instructions
    
    def validate(self, context: Context) -> Iterator[Issue]:
        for o in self.instructions:
            yield from o.validate(context)

        #TODO: generate warnings for unused symbols declared in this context
    
    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) and self.instructions == obj.instructions
    
    def __str__(self) -> str:
        return '\n'.join(str(o) for o in self.instructions)

class Function(Element):
    def __init__(self, name: str, args: list[(str,Type)], returnType: Type, body: Program) -> None:
        self.name = name
        self.args = args
        self.returnType = returnType
        self.body = body

    def validate(self, context: Context) -> Iterator[Issue]:
        for _,type in self.args:
            yield from type.validate(context)

        if context.is_declared(self.name):
            yield Issue(IssueType.Error, self, f"Redefinition of symbol '{self.name}'")

        subcontext = Context(context)

        for arg,type in self.args:
            if subcontext.is_declared(arg):
                yield Issue(IssueType.Error, self, f"Redefinition of symbol '{arg}'")
            else:
                subcontext.declare_variable(Declaration(False, arg, type, None))

        yield from self.body.validate(subcontext)
        context.declare_function(self)

    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) \
            and self.name == obj.name \
            and self.args == obj.args \
            and self.returnType == obj.returnType \
            and self.body == obj.body
    
    def __str__(self) -> str:
        return f"func {self.name}({', '.join(f'{arg}: {type}' for arg,type in self.args)}): {self.returnType} {{\n{self.body}\n}}"


#TODO: if, while, do-while, return