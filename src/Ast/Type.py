class Type(): # Type class encapsulates all of our other types.
    TYPELIST = []
    def __init__(self, typename, value, functionList, repr):
        self.type = typename
        self.value = value
        self.functionList = functionList
        self.repr = repr
        if not typename in Type.TYPELIST:
            Type.TYPELIST.append(typename)

    def eval(self):
        print("WARNING, TYPE NOT REGISTERED WITH EVAL PROPERTY.")