from typing import Iterator, Optional
from .element import Element
from .expressions import Expression
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
        elif self.valueType != None and not self.valueType.isAssignableFrom(self.value.type(context)):
            yield Issue(IssueType.Error, self.value, "TypeError: TODO escrever")

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

        if not self.dest.type(context).isAssignableFrom(self.value.type(context)):
            yield Issue(IssueType.Error, self.value, "TypeError: TODO escrever")

    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) and self.dest == obj.dest and self.value == obj.value

    def __str__(self) -> str:
        return f"{self.dest} = {self.value}"


class Program(Element):
    def __init__(self, instructions) -> None:
        self.instructions = instructions
    
    def validate(self, context: Context) -> Iterator[Issue]:
        for o in self.instructions:
            yield from o.validate(context)
    
    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) and len(self.instructions) == len(obj.instructions) and all(t==k for t,k in zip(self.instructions,obj.instructions))
    
    def __str__(self) -> str:
        return '\n'.join(str(o) for o in self.instructions)


#TODO: if, while, do-while