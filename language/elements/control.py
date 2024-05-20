from typing import Iterator, Optional
from .element import Element
from .expressions import Expression, Kind, Value
from .types import VOID, Type,BOOL
from ..context import Context
from ..issue import Issue, IssueType, TypeError
import pygraphviz as pgv


def zipEmptyStrings(l):
    for i in l:
        yield (i,"")


class Declaration(Element):
    def __init__(self, const: bool, variable: str, type: Optional[Type], value: Optional[Expression]) -> None:
        super().__init__()
        self.const = const
        self.variable = variable
        self.valueType = type
        self.value = value

    def type(self, context: Context):
        if self.valueType != None:
            return self.valueType
        
        vtype = self.value.type(context)
        if not isinstance(vtype, VOID):
            return vtype
        
        return None

    def validate(self, context: Context) -> Iterator[Issue]:
        if self.valueType != None:
            yield from self.valueType.validate(context)

        if self.value != None:
            yield from self.value.validate(context)
        
        if self.value == None:
            if self.const:
                yield Issue(IssueType.Error, self, "Constants must be initialized")
            elif self.valueType == None:
                yield Issue(IssueType.Error, self, "Can't infer type of uninitialized variable")
        elif isinstance(self.value.type(context), VOID):
            yield Issue(IssueType.Error, self.value, "Can't assign variable to void return type")
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
    
    def _toHTML(self, errors, depth=0) -> str:
        s = f"""<span class="line" index={depth}></span><span class="control">{'const' if self.const else 'var'} </span>"""
        s += f"""<span class="variable">{self.variable}</span>"""
        if self.valueType:
            s += f"""<span class="operator"> : </span>"""
            s += self.valueType.toHTML(errors)
        if self.value:
            s += f"""<span class="operator"> = </span>"""
            s += self.value.toHTML(errors)
        return s

    def append_to_graph(self, graph: pgv.AGraph,NewScope=False, end=None):
        graph.add_node(str(self.id), label=str(self), shape="oval")
        return str(self.id),[(str(self.id),"")]
        
            
        
        
    

class Assignment(Element):
    def __init__(self, dest: Expression, value: Expression) -> None:
        super().__init__()
        self.dest = dest
        self.value = value

    def validate(self, context: Context) -> Iterator[Issue]:
        yield from self.dest.validate(context)
        yield from self.value.validate(context)

        if self.dest.kind(context) not in [Kind.Variable, None]:
            yield Issue(IssueType.Error, self, f"Cannot assign to expression of kind {self.dest.kind(context)}")
        else:
            yield from TypeError.check(self.value, self.dest.type(context), context)

    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) and self.dest == obj.dest and self.value == obj.value

    def __str__(self) -> str:
        return f"{str(self.dest)} = {str(self.value)}"
    
    def _toHTML(self, errors, depth=0) -> str:
        s = f"""<span class="line" index={depth}></span>"""
        s += self.dest.toHTML(errors)
        s += f"""<span class="operator"> = </span>"""
        s += self.value.toHTML(errors)
        return s

    def append_to_graph(self, graph: pgv.AGraph,NewScope=False, end=None):
        graph.add_node(str(self.id), label=str(self), shape="oval")
        return str(self.id),[(str(self.id),"")]


class Program(Element):
    def __init__(self, instructions: list[Element]) -> None:
        super().__init__()
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
    
    def _toHTML(self, errors, depth=0) -> str:
        semicolon = lambda x: '' if any(isinstance(x,c) for c in [If,While,Function,Do_while]) else '<span class="operator">;</span>'
        return '<br>'.join((o.toHTML(errors,depth) + semicolon(o)) for o in self.instructions)
    
    def isIf(self) -> bool:
        return len(self.instructions)==1 and type(self.instructions[0]) == If
    
    def append_to_graph(self, graph: pgv.AGraph,NewScope=False, end=None):
        if NewScope:
            graph.add_node(str(self.id)+"S", label="START", shape="oval")
            graph.add_node(str(self.id)+"E", label="END", shape="oval")
            
            r = str(self.id)+"S"
            prev = [(str(self.id)+"S","")]
            instructions= self.instructions
            Nend = str(self.id)+"E"
        elif self.instructions:
            f,l = self.instructions[0].append_to_graph(graph,end=end)
            r = f
            prev=l
            instructions = self.instructions[1:]
            Nend = end
        
        
        for instruction in instructions :
            f,l = instruction.append_to_graph(graph,end=Nend)
            for p,k in prev:
                graph.add_edge(p,f,label=k)
            prev=l
            
        if NewScope:
            for p,k in prev:
                graph.add_edge(p,str(self.id)+"E",label=k)
            return r,[(str(self.id)+"E","")]
        else:
            return r,prev
        
    

class FunctionArg(Element): 
    def __init__(self, name: str, type: Type) -> None:
        super().__init__()
        self.name = name
        self.type = type

    def validate(self, context: Context) -> Iterator[Issue]:
        yield from self.type.validate(context)
        
        if context.is_declared(self.name):
            yield Issue(IssueType.Error, self, f"Redefinition of symbol '{self.name}'")
        else:
            context.declare_variable(Declaration(False, self.name, self.type, None))

    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) \
            and self.name == obj.name \
            and self.type == obj.type

    def __str__(self) -> str:
        return f"{self.name}: {str(self.type)}"
    
    def _toHTML(self, errors, depth=0) -> str:
        return f'<span class="operator"><span class="variable">{self.name}</span> : {self.type.toHTML(errors)}</span>'

class Function(Element):
    def __init__(self, name: str, args: list[FunctionArg], returnType: Type, body: Program) -> None:
        super().__init__()
        self.name = name
        self.args = args
        self.returnType = returnType
        self.body = body

    def validate(self, context: Context) -> Iterator[Issue]:
        if context.is_declared(self.name):
            yield Issue(IssueType.Error, self, f"Redefinition of symbol '{self.name}'")

        subcontext = Context(context,self.returnType)
        for arg in self.args:
            yield from arg.validate(subcontext)

        yield from self.body.validate(subcontext)
        context.declare_function(self)
        context.stats.mergeWith(subcontext.stats)

    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) \
            and self.name == obj.name \
            and self.args == obj.args \
            and self.returnType == obj.returnType \
            and self.body == obj.body
    
    
    def __str__(self) -> str:
        return f"func {self.name}({', '.join(self.args)}): {self.returnType} {{\n{self.body}\n}}"
    
    def _toHTML(self, errors, depth=0) -> str:
        s=f"""<span class="line" index={depth}></span><span class="control">func </span>"""
        args = f"""<span class="encloser">({'<span class="operator">, </span>'.join(arg.toHTML(errors) for arg in self.args)})</span>"""
        s += f"""<span class="function">{self.name}{args}</span>"""
        if not isinstance(self.returnType, VOID):
            s += f"""<span class="operator"> : </span>"""
            s += self.returnType.toHTML(errors)
        s += f"""<span class="line" index={depth}></span><span class="scope"> {{
<br>{self.body.toHTML(errors,depth+1)}
<br><span class="line" index={depth}></span>}}</span>"""
        return s

    def append_to_graph(self, graph: pgv.AGraph,NewScope=False, end=None):
        graph.add_subgraph(name="cluster_"+self.name)
        c = graph.subgraphs()[-1]
        
        c.graph_attr.update(style='dotted', color='blue', penwidth='2',label=self.name)
        c.add_node(str(self.id), label= f"func {self.name}({', '.join(str(x) for x in self.args)}): {self.returnType}", shape="oval")
        f,l = self.body.append_to_graph(c,True)
        c.add_edge(str(self.id),f)
        
        return str(self.id),l
    

class Return(Element):
    def __init__(self, exp: Optional[Expression]) -> None:
        super().__init__()
        self.value = exp
    
    def validate(self, context: Context) -> Iterator[Issue]:
        expectedType = context.get_returnType()

        if expectedType == None:
            yield Issue(IssueType.Error, self, "Return is only allowed inside functions")
        elif self.value != None:
            yield from self.value.validate(context)
            yield from TypeError.check(self.value, context.get_returnType(), context)
        elif not isinstance(expectedType, VOID):
            yield Issue(IssueType.Error, self, "Expected expression after return")

    def __str__(self) -> str:
        if self.value != None:
            return f"return {str(self.value)}"
        else:
            return "return"
    
    def _toHTML(self, errors, depth=0) -> str:
        s=f""" {self.value.toHTML(errors)}""" if self.value != None else ""
        return f"""<span class="line" index={depth}></span><span class="control">return{s}</span>"""
    
    def __eq__(self, obj) -> bool:
         return type(self) == type(obj) \
            and self.value == obj.value
    
    def append_to_graph(self, graph: pgv.AGraph,NewScope=False, end=None):
        graph.add_node(str(self.id), label= str(self), shape="oval")
        graph.add_edge(str(self.id),end)
        return str(self.id),[]
    
    

class If(Element):
    def __init__(self, condition : Expression, ifScope : Program, elseScope : Program|None) -> None:
        super().__init__()
        self.condition = condition
        self.ifScope = ifScope
        self.elseScope = elseScope
    
    def validate(self, context: Context) -> Iterator[Issue]:
        yield from self.condition.validate(context)
        if not BOOL().isAssignableFrom(self.condition.type(context)):
            yield Issue(IssueType.Error, self.condition,"Condition is not Boolean")
        elif self.condition.kind(context) == Kind.Constant:
            yield Issue(IssueType.Info, self.condition, "Condition is constant")
        
        ifContext = Context(context,context.get_returnType())
        yield from self.ifScope.validate(ifContext)
        context.stats.mergeWith(ifContext.stats)
        
        if self.elseScope:
            elseContext = Context(context,context.get_returnType())
            yield from self.elseScope.validate(elseContext)
            context.stats.mergeWith(elseContext.stats)
        
        if self.ifScope.isIf() and not self.ifScope.instructions[0].hasElse():
            yield Issue(IssueType.Info,self.ifScope,"Condition can be joint with top if")
    
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
    
    def _toHTML(self, errors, depth=0) -> str:
        s=f"""<span class="line" index={depth}></span><span class="control">if </span>"""
        s += f"""<span class="encloser">({self.condition.toHTML(errors)}) </span>"""
        s += f"""<span class="scope"> {{
<br>{self.ifScope.toHTML(errors,depth+1)}
<br><span class="line" index={depth}></span>}}</span>"""
        if self.hasElse():
            if self.elseScope.isIf():
                s+=f"""<span class="control">elif</span>{self.elseScope.toHTML(errors,depth)}"""
            else:
                s+=f"""<span class="control"> else</span>"""
                s+=f"""<span class="scope"> {{
<br>{self.elseScope.toHTML(errors,depth+1)}
<br><span class="line" index={depth}></span>}}</span>"""

        s = s.replace(f"""<span class="control">elif</span><span class="line" index={depth}></span><span class="control">if </span>""",
                     """<span class="control"> elif </span>""")
        return s
    
    def append_to_graph(self, graph: pgv.AGraph,NewScope=False, end=None):
        graph.add_node(str(self.id), label= str(self.condition), shape="Mdiamond")
        f,fl = self.ifScope.append_to_graph(graph,end=end)
        graph.add_edge(str(self.id), f,label="True")
        if self.elseScope:
            f,el = self.elseScope.append_to_graph(graph,end=end)
            graph.add_edge(str(self.id), f,label="False")
            return str(self.id),fl+el
        else :   
            return str(self.id),fl+[(str(self.id),"False")]


class While(Element):
    def __init__(self, condition:Expression, scope: Program) -> None:
        super().__init__()
        self.condition = condition
        self.scope = scope
        
    def validate(self, context: Context) -> Iterator[Issue]:
        yield from self.condition.validate(context)
        if not BOOL().isAssignableFrom(self.condition.type(context)):
            yield Issue(IssueType.Error, self.condition,"Condition must be of type bool")
        elif self.condition.kind(context) == Kind.Constant and not isinstance(self.condition, Value):
            yield Issue(IssueType.Info, self.condition, "Condition can be simplified")
        
        scopeContext = Context(context,context.get_returnType())
        yield from self.scope.validate(scopeContext)
        context.stats.mergeWith(scopeContext.stats, isLoop=True)
    
    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) \
            and self.condition == obj.condition \
            and self.scope == obj.scope
    

    def __str__(self) -> str:
        return f"""
while ({str(self.condition)}) {{
    {str(self.scope)}
}}"""
    def _toHTML(self, errors, depth=0) -> str:
        s=f"""<span class="line" index={depth}></span><span class="control">while </span>"""
        s += f"""<span class="encloser">({self.condition.toHTML(errors)}) </span>"""
        s += f"""<span class="scope"> {{
<br>{self.scope.toHTML(errors,depth+1)}
<br><span class="line" index={depth}></span>}}</span>"""
        return s
    
    def append_to_graph(self, graph: pgv.AGraph,NewScope=False, end=None):
        graph.add_node(str(self.condition.id), label= f"while ({str(self.condition)})", shape="Mdiamond")
        f,l = self.scope.append_to_graph(graph,end=end)
        graph.add_edge(str(self.condition.id), f,label="True")
        for i,k in l:
            graph.add_edge(i,str(self.condition.id),k)
        return str(self.condition.id),[(str(self.condition.id),"False")]
    
class Do_while(Element):
    def __init__(self, condition:Expression, scope: Program) -> None:
        super().__init__()
        self.condition = condition
        self.scope = scope
        
    def validate(self, context: Context) -> Iterator[Issue]:
        yield from self.condition.validate(context)
        condType = self.condition.type(context)
        if not BOOL().isAssignableFrom(condType):
            yield TypeError(self.condition, BOOL(), condType)
        elif self.condition.kind(context) == Kind.Constant and not isinstance(self.condition, Value):
            yield Issue(IssueType.Info, self.condition, "Condition can be simplified")

        scopeContext = Context(context,context.get_returnType())
        yield from self.scope.validate(scopeContext)
        context.stats.mergeWith(scopeContext.stats, isLoop=True)
    
    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) \
            and self.condition == obj.condition \
            and self.scope == obj.scope
    

    def __str__(self) -> str:
        return f"""
do {{
    {str(self.scope)}
}} while ({str(self.condition)})"""

    def _toHTML(self, errors, depth=0) -> str:
        s = f"""<span class="line" index={depth}></span><span class="control">do </span>"""
        s += f"""<span class="scope"> {{
{self.scope.toHTML(errors,depth+1)}
<span class="line" index={depth}></span>}}</span>"""
        s += f"""<span class="line"><span class="control">while </span>"""
        s += f"""<span class="encloser">({self.condition.toHTML(errors)}) </span></span>"""
        return s
    
    def append_to_graph(self, graph: pgv.AGraph,NewScope=False, end=None):
        graph.add_node(str(self.condition.id), label= f"while ({str(self.condition)})", shape="Mdiamond")
        f,l = self.scope.append_to_graph(graph,end=end)
        for p,v in l:
            graph.add_edge(p,str(self.condition.id),label=v)
        graph.add_edge(str(self.condition.id),f,label="True")
        return f,[(str(self.condition.id),"False")]
    