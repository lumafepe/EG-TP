from lark import Lark
import sys
from transformer import T
from language.context import Context
from collections import defaultdict
import pygraphviz as pgv
from language.issue import IssueType,Issue
from language.elements.element import Element
from language.elements.control import Function,Program,FunctionArg
from language.elements.types import VOID,ANY


#const_tuple: "(" ( (constant ",")+ constant? | constant "," | ) ")"
#const_array: "[" (constant ",")* constant? "]"
#const_list: "<" (constant ",")* constant? ">"

"""
9  arr[]
8  #n               unary, left to right
7  ! ~ #		    unary, right to left
6  ^                right to left
5  * / %
4  + -
3  < <= > >=
2  == !=
1  &&
0  ||
"""

lark_parser = r"""
    PRIMITIVE.1: "int" | "string" | "char" | "bool"
    BOOL.1: "true" | "false"
    INT: /-?\d+/
    CHAR: /'([^\b\t\n\r']|\\[\\0btnr'])'/
    STRING: /"([^\b\t\n\r"]|\\[\\0btnr"])*"/
    IDENTIFIER: /[A-Za-z_]\w*/

    tuple_type: "(" (type ",")+ type? ")"
    array_type: "[" type "]"
    list_type: "<" type ">"
    type: PRIMITIVE | tuple_type | array_type | list_type

    _sequence: (expression ",")* expression?

    constant: INT | CHAR | STRING | BOOL
    tuple: "(" (expression ",")+ expression? ")"
    array: "[" _sequence "]"
    new_array: type "[" expression "]"
    list: "<" (_sequence | (expression ",")* expression ":" expression) ">"

    OP0: "\|\|"
    OP1: "&&"
    OP2: "==" | "!="
    OP3: "<" | "<=" | ">" | ">="
    OP4: "+" | "-"
    OP5: "*" | "/" | "%"
    OP6: "^"
    OP7: "~" | "!" | "#"
    OP8: /#\d+/

    _exp0: _exp1 | op_or
    op_or: _exp0 OP0 _exp1
    _exp1: _exp2 | op_and
    op_and: _exp1 OP1 _exp2
    _exp2: _exp3 | op_equality
    op_equality: _exp2 OP2 _exp3
    _exp3: _exp4 | op_comparison
    op_comparison: _exp3 OP3 _exp4
    _exp4: _exp5 | op_sum
    op_sum: _exp4 OP4 _exp5
    _exp5: _exp6 | op_multiplication
    op_multiplication: _exp5 OP5 _exp6
    _exp6: _exp7 | op_exponentiation
    op_exponentiation: _exp7 OP6 _exp6
    _exp7: _exp8 | op_manipulation
    op_manipulation:  OP7 _exp7
    _exp8: _exp9 | op_element
    op_element: _exp8 OP8
    _exp9: _exp_base | op_indexation
    op_indexation: _exp9 "[" expression "]"

    variable : IDENTIFIER
    _exp_base: constant
        | variable
        | tuple
        | array
        | new_array
        | list
        | function_call
        | "(" expression ")"
    expression: _exp0

    KIND: "var" | "const"
    declaration: KIND IDENTIFIER ":" type
    assignment: expression "=" expression
    decl_ass: KIND IDENTIFIER (":" type)? "=" expression

    scope: "{" program "}"
    condition: "(" expression ")"

    if_cond: "if" condition scope ("elif" condition scope)* ("else" scope)?
    while_cond: "while" condition scope
    do_while: "do" scope "while" condition ";"

    function: "func" IDENTIFIER "(" params ")" (":" type)? scope
    params: ((IDENTIFIER ":" type ",")* IDENTIFIER ":" type)?
    function_call: IDENTIFIER "(" _sequence ")"
    func_return: "return" expression?

    program: (declaration ";" | assignment ";" | decl_ass ";" | function_call ";" | func_return ";" | if_cond | while_cond | do_while | function)*

    %import common (WS, C_COMMENT, CPP_COMMENT)
    %ignore WS
    %ignore C_COMMENT
    %ignore CPP_COMMENT
"""


def isItsOwnSuccessor(g:pgv.AGraph,n):
    nexts = list(g.successors(n))
    while nexts:
        succ = nexts.pop()
        if succ.endswith('E'):
            continue
        if n == succ:
            return True
        nexts.extend(g.successors(succ))
    return False
    


def parse(input):

    p = Lark(lark_parser,start="program") # cria um objeto parser
    tree = p.parse(input)  # retorna uma tree
    transformer = T()
    linguagem = transformer.transform(tree)
    
    printFuntion = Function("print",[FunctionArg("text",ANY())],VOID(),Program([]))
    
    
    c = Context()
    
    c.declare_function(printFuntion)

    errors = defaultdict(set)
    for i in linguagem.validate(c):
        errors[i.elem.id].add(i)
    
    G = pgv.AGraph(directed=True)
    linguagem.append_to_graph(G,True)
    html_content = G.draw(format='svg', prog='dot').decode()
    
    # unreachable code
    s = list(filter(lambda x : len(G.in_edges(x)) == 0 and x.isnumeric() ,G.nodes()))
    while s:
        si = s.pop(0)
        i = int(si)
        errors[i].add(Issue(IssueType.Warning,Element.elems[i],"Unreachable Code"))
        nexts = G.successors(si)
        G.remove_node(si)
        s.extend(list(filter(lambda x : len(G.in_edges(x)) == 0 and x.isnumeric() ,nexts)))
    
    # while can be if 
    s = list(filter(lambda x :x.attr['label'].startswith("while") ,G.nodes()))
    for i in s:
        if not isItsOwnSuccessor(G,i):
            errors[int(i)].add(Issue(IssueType.Info,Element.elems[int(i)],"This should be an If contion"))
            
    
    
    maxDepth = c.stats.maxLoops
    counters = transformer.counter
    main_instructions = len(linguagem.instructions)
    return (linguagem,errors,maxDepth,counters,main_instructions,html_content)

if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        parse(f.read())