from lark import Transformer
from language import types,value


class T(Transformer):
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
        return value.Value(int(token),types.INT())
    
    def CHAR(self,token):
        return value.Value(token,types.CHAR())
    
    def STRING(self,token):
        return value.Value(token,types.STRING())
    
    def tuple_type(self,token):
        return types.TUPLE(token)
    
    def array_type(self,token):
        return types.ARRAY(token[0])
    
    def list_type(self,token):
        return types.LIST(token[0])
    
    def type(self,token):
        return token[0]
    