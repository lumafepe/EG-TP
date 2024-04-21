from typing import Iterator, Optional
from .element import Element
from .expressions import Expression, Kind
from .types import Type,BOOL
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

        if self.dest.kind(context) != Kind.Variable:
            yield Issue(IssueType.Error, self, f"Cannot assign to expression of kind {self.dest.kind(context)}")
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
        semicolon = lambda x: '' if any(isinstance(x,c) for c in [If,While,Function,Do_while]) else ';'
        return '\n'.join((str(o) + semicolon(o)) for o in self.instructions)
    
    def isIf(self) -> bool:
        return len(self.instructions)==1 and type(self.instructions[0]) == If

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

        subcontext = Context(context,self.returnType)

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


class Return(Element):
    def __init__(self, exp: Expression) -> None:
        self.value = exp
    
    def validate(self, context: Context) -> Iterator[Issue]:
        yield from self.value.validate(context)
        if not self.value.type(context).isAssignableFrom(context.get_returnType()):
            yield Issue(IssueType.Error, self, f"Wrong type, {self.value.type(context)} is returned but {context.get_returnType()} was expected ")
        
    def type(self,context:Context) -> Type :
        return context.get_returnType()

    def __str__(self) -> str:
        return f"return {str(self.value)}"
    
    def __eq__(self, obj) -> bool:
         return type(self) == type(obj) \
            and self.value == obj.value

class If(Element):
    def __init__(self, condition : Expression, ifScope : Program, elseScope : Program|None) -> None:
        self.condition = condition
        self.ifScope = ifScope
        self.elseScope = elseScope
    
    def validate(self, context: Context) -> Iterator[Issue]:
        yield from self.condition.validate(context)
        if not self.condition.type(context).isAssignableFrom(BOOL()):
            yield Issue(IssueType.Error, self.condition,"Condition is not Boolean")
        
        ifContext = Context(context,context.get_returnType())
        yield from self.ifScope.validate(ifContext)
        
        if self.elseScope:
            elseContext = Context(context,context.get_returnType())
            yield from self.elseScope.validate(elseContext)
    
    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) \
            and self.condition == obj.condition \
            and self.ifScope == obj.ifScope \
            and self.elseScope == obj.elseScope
            
    def hasElse(self) -> bool:
        return self.elseScope != None
    
    def __str__(self) -> str:
        s=f"""if ({str(self.condition)}) {{
    {str(self.ifScope)}
}}
"""
        if self.hasElse():
            if self.elseScope.isIf():
                #elif
                s+=f"""el{str(self.elseScope)}"""
            else:
                s+=f"""else {{
    {str(self.elseScope)}
}}"""
        return s

class While(Element):
    def __init__(self, condition:Expression, scope: Program) -> None:
        self.condition = condition
        self.scope = scope
        
    def validate(self, context: Context) -> Iterator[Issue]:
        yield from self.condition.validate(context)
        if not self.condition.type(context).isAssignableFrom(BOOL()):
            yield Issue(IssueType.Error, self.condition,"Condition is not Boolean")
        
        scopeContext = Context(context,context.get_returnType())
        yield from self.scope.validate(scopeContext)
    
    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) \
            and self.condition == obj.condition \
            and self.scope == obj.scope

    def __str__(self) -> str:
        return f"""
while ({str(self.condition)}) {{
    {str(self.scope)}
}}"""
            
class Do_while(Element):
    def __init__(self, condition:Expression, scope: Program) -> None:
        self.condition = condition
        self.scope = scope
        
    def validate(self, context: Context) -> Iterator[Issue]:
        yield from self.condition.validate(context)
        if not self.condition.type(context).isAssignableFrom(BOOL()):
            yield Issue(IssueType.Error, self.condition,"Condition is not Boolean")
        
        scopeContext = Context(context,context.get_returnType())
        yield from self.scope.validate(scopeContext)
    
    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) \
            and self.condition == obj.condition \
            and self.scope == obj.scope

    def __str__(self) -> str:
        return f"""
do {{
    {str(self.scope)}
}} while ({str(self.condition)})"""