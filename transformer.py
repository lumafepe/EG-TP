from lark import Transformer

from language.elements import types, expressions

from collections import Counter

class T(Transformer):
    
    def __init__(self) -> None:
        super().__init__()
        self.counter = Counter()
    
    def PRIMITIVE(self,token):
        match token:
            case 'int':
                return types.INT()
            case 'string':
                return types.STRING()
            case 'char':
                return types.CHAR()
            case 'bool':
                return types.BOOL()
    def IDENTIFIER(self,token):
        return str(token)
    def INT(self,token):
        return expressions.Value(int(token),types.INT())
    def CHAR(self,token):
        return expressions.Value(token,types.CHAR())
    def STRING(self,token):
        return expressions.Value(token,types.STRING())
    
    def tuple_type(self,token):
        return types.TUPLE(token)
    def array_type(self,token):
        return types.ARRAY(token[0])
    def list_type(self,token):
        return types.LIST(token[0])
    def type(self,token):
        return token[0]
    
    def constant(self,token):
        return token[0]
    def tuple(self,token):
        print(token)
        return expressions.Tuple(token)
    def array(self,token):
        return expressions.Array(token)
    def list(self,token):
        return expressions.List(token)
    
    def OP0(self,token):
        return token
    def OP1(self,token):
        return token
    def OP2(self,token):
        return token
    def OP3(self,token):
        return token
    def OP4(self,token):
        return token
    def OP5(self,token):
        return token
    def OP6(self,token):
        return token
    def OP7(self,token):
        return token
    def OP8(self,token):
        return token
    
    def op_or(self,token):
        return expressions.Or(token[0],token[2])
    def op_and(self,token):
        return expressions.And(token[0],token[2])
    def op_equality(self,token):
        match token[1]:
            case '!=':
                return expressions.Inequality(token[0],token[2])
            case '==':
                return expressions.Equality(token[0],token[2])
    def op_comparison(self,token):
        match token[1]:
            case '<':
                return expressions.Lt(token[0],token[2])
            case '<=':
                return expressions.Lte(token[0],token[2])
            case '>':
                return expressions.Gt(token[0],token[2])
            case '>=':
                return expressions.Gte(token[0],token[2])
    def op_sum(self,token):
        match token[1]:
            case '-':
                return expressions.Subtraction(token[0],token[2])
            case '+':
                return expressions.Addition(token[0],token[2])
    def op_multiplication(self,token):
        match token[1]:
            case '*':
                return expressions.Multiplication(token[0],token[2])
            case '/':
                return expressions.Division(token[0],token[2])
            case '%':
                return expressions.Modulo(token[0],token[2])
    def op_exponentiation(self,token):
        return expressions.Expotentiation(token[0],token[2])
    def op_manipulation(self,token):
        match token[0]:
            case '~':
                return expressions.BitwiseNot(token[1])
            case '!':
                return expressions.Not(token[1])
            case '#':
                return expressions.Length(token[1])
    def op_element(self,token):
        return expressions.Or(token[0],token[2])#TODO
    def op_indexation(self,token):
        return expressions.Or(token[0],token[2])#TODO

    
    def expression(self,token):
        return token[0]
    
    def KIND(self,token):
        return token
    def declaration(self,token):
        self.counter['declaration']+=1
        return token #TODO
    def assignment(self,token): 
        self.counter['assignment']+=1
        return token #TODO
    def decl_ass(self,token):
        self.counter['declaration']+=1
        self.counter['assignment']+=1
        return token #TODO

    def scope(self,token):
        return token #TODO
    def condition(self,token):
        return token #TODO
    
    def if_cond(self,token):
        return token #TODO
    def while_cond(self,token):
        return token #TODO
    def do_while(self,token):
        return token #TODO
    
    def function(self,token):
        self.counter['functions']+=1
        return token #TODO
    def params(self,token):
        return token #TODO
    def function_call(self,token):
        self.counter['function_call']+=1
        return token #TODO
    def func_return(self,token):
        return token #TODO
    
    def program(self,token):
        self.counter['main_instructions']+=1
        return token #TODO
    
        
        
        
    
    