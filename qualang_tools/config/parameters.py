class ConfigVar:
    def __init__(self):
        self.values = {}
        self.value_set = {}

    def parameter(self, name: str):
        if name in self.values:
            return lambda: self.get(name)
        if name.find(" ") != -1:
            raise ValueError(
                "Parameter name cannot contain spaces. " "Use underscore of camelCase."
            )
        self.values[name] = None
        self.value_set[name] = False
        return lambda: self.get(name)

    def get(self, name: str):
        assert self.value_set[name], f"Parameter '{name}' has not been defined yet."
        return self.values[name]

    def set(self, **kwargs):
        for key, value in kwargs.items():
            if key not in self.values:
                self.parameter(key)
            self.values[key] = value
            self.value_set[key] = True
        return


def isparametric(obj):
    if callable(obj):
        try:
            obj()
            return False
        except AssertionError:
            return True
    elif hasattr(obj, "__dict__"):
        for elm in obj.__dict__:
            _obj = getattr(obj, elm)
            if hasattr(_obj, "__dict__"):
                return isparametric(_obj)
            elif type(_obj) is dict:
                for (k, v) in _obj.items():
                    if isparametric(v):
                        return True
            elif type(_obj) is list:
                for elm in _obj:
                    if isparametric(elm):
                        return True
    else:
        return False


def iscallable(obj):
    if callable(obj):
        return True
    elif type(obj) is dict:
        for (k, v) in obj.items():
            if callable(v):
                return True
    else:
        return False
