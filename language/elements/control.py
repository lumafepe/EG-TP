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
        self.type = type
        self.value = value

    def type(self, context: Context):
        return self.type if self.type != None else self.value.type(context)

    def validate(self, context: Context) -> Iterator[Issue]:
        if self.type != None:
            yield from self.type.validate(context)

        if self.value != None:
            yield from self.value.validate(context)
        
        if self.value == None:
            if self.const:
                yield Issue(IssueType.Error, self, "Constants must be initialized")
            elif self.type == None:
                yield Issue(IssueType.Error, self, "Cannot infer type of uninitialized variable")
        elif self.type != None and not self.type.isAssignableFrom(self.value.type(context)):
            yield Issue(IssueType.Error, self.value, "TypeError: TODO escrever")

        if context.is_declared(self.variable):
            yield Issue(IssueType.Error, self, "Symbol already declared")
        else:
            context.declare_variable(self)

class Assignment(Element):
    def __init__(self, variable: str, value: Expression) -> None:
        self.variable = variable
        self.value = value

    def validate(self, context: Context) -> Iterator[Issue]:
        yield from self.value

        if not context.is_declared_variable(self.variable):
            yield Issue(IssueType.Error, self, "Variable not declared")
        elif not context.get_declaration().isAssignableFrom(self.value.type(context)):
            yield Issue(IssueType.Error, self.value, "TypeError: TODO escrever")

    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) and self.variable == obj.variable and self.value == type.value

    def __str__(self) -> str:
        return f"{self.variable} = {self.value}"



#TODO: if, while, do-while, function