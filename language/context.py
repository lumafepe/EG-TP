class Context():
    next_var = 0

    stdlib_symbols = {}

    def __init__(self, function_name="", arg_name="", parent=None):
        self.parent = parent
        self.symbols = {} if parent is None else parent.symbols.copy()
        self.function_name = function_name
        self.arg_name = arg_name

    def in_global_scope(self):
        return self.parent is None

    def next_variable(self):
        result = f"var_{Context.next_var}"
        Context.next_var += 1
        return result

