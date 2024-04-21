from collections import Counter

class Context():
    def __init__(self,parent=None,returnType=None):
        self.variables = {} if parent is None else parent.variables.copy()
        self.functions = {} if parent is None else parent.functions.copy()
        self.usedVariables = Counter()
        self.usedFunctions = Counter()
        self.returnType = returnType

    def in_global_scope(self) -> bool:
        return self.parent is None

    def used_variables(self) -> Counter:
        return self.usedVariables
    def used_functions(self) -> Counter:
        return self.functions
    def used_symbols(self) -> Counter :
        return self.usedVariables + self.functions
    
    def use_variables(self,symbol) -> None:
        self.usedVariables[symbol]+=1
    def use_functions(self,symbol) -> None:
        self.usedFunctions[symbol]+=1
    def use_symbol(self,symbol) -> None:
        if symbol in self.variables:
            self.usedVariables[symbol]+=1
        else:
            self.usedFunctions[symbol]+=1
    
    def is_declared(self,symbol) -> None:
        return symbol in self.variables or symbol in self.functions
    def is_declared_variable(self,symbol) -> None:
        return symbol in self.variables
    def is_declared_function(self,symbol) -> None:
        return symbol in self.functions
    
    
    #elem is the whole declaration, not just the value
    def declare_variable(self,declaration) -> None:
        self.variables[declaration.variable]=declaration
    def declare_function(self,elem) -> None:
        self.functions[elem.name]=elem
        
    def get_variable_declaration(self,symbol):
        if symbol in self.variables: return self.variables[symbol]
        else : return None
    def get_funtion_declaration(self,symbol):
        if symbol in self.functions: return self.functions[symbol]
        else : return None
    def get_symbol_declaration(self,symbol):
        if symbol in self.variables: return self.variables[symbol]
        elif symbol in self.functions: return self.functions[symbol]
        else : return None
    
    def get_returnType(self):
        return self.returnType
