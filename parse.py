from lark import Lark
import sys
from transformer import T


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

    tuple_type: "(" (type ","){2,} type? ")"
    array_type: "[" type "]"
    list_type: "<" type ">"
    type: PRIMITIVE | tuple_type | array_type | list_type

    _sequence: (expression ",")* expression?

    constant: INT | CHAR | STRING | BOOL
    tuple: "(" (expression ","){2,} expression? ")"
    array: "[" _sequence "]" | type "[" INT "]"
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

    _exp0: _exp1 | or
    or: _exp0 OP0 _exp1
    _exp1: _exp2 | and
    and: _exp1 OP1 _exp2
    _exp2: _exp3 | equality
    equality: _exp2 OP2 _exp3
    _exp3: _exp4 | comparison
    comparison: _exp3 OP3 _exp4
    _exp4: _exp5 | sum
    sum: _exp4 OP4 _exp5
    _exp5: _exp6 | multiplication
    multiplication: _exp5 OP5 _exp6
    _exp6: _exp7 | exponentiation
    exponentiation: _exp7 OP6 _exp6
    _exp7: _exp8 | manipulation
    manipulation:  OP7 _exp7
    _exp8: _exp9 | element
    element: _exp8 OP8
    _exp9: _exp_base | indexation
    indexation: _exp9 "[" expression "]"

    _exp_base: constant
        | IDENTIFIER
        | tuple
        | array
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
    func_return: "return" expression

    program: (declaration ";" | assignment ";" | decl_ass ";" | function_call ";" | func_return ";" | if_cond | while_cond | do_while | function)*

    %import common (WS, C_COMMENT, CPP_COMMENT)
    %ignore WS
    %ignore C_COMMENT
    %ignore CPP_COMMENT
"""


input = """
"""


p = Lark(lark_parser,start="program") # cria um objeto parser
tree = p.parse(input)  # retorna uma tree
linguagem = T().transform(tree)
print(linguagem)