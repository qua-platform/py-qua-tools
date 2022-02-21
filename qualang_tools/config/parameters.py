class Parameter(object):
    def __init__(self, name: str):
        self.is_set = False
        self._value = None
        self.name = name

    def __call__(self, *args, **kwargs):
        if self.is_set:
            if callable(self._value):
                return self._value(*args, **kwargs)
            else:
                return self._value
        else:
            raise AssertionError("Parameter {} is not set".format(self.name))

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self.is_set = True
        self._value = v


class ConfigVars(object):
    def __init__(self):
        self.params = {}

    def parameter(self, name, setter=None):
        if name.find(" ") != -1:
            raise ValueError(
                "Parameter name cannot contain spaces. " "Use underscore of camelCase."
            )
        if name not in self.params.keys():
            self.params[name] = Parameter(name)
            self.params[name].value = setter
        return self.params[name]

    def set(self, **kwargs):
        for key, value in kwargs.items():
            if key not in self.params.keys():
                self.params[key] = Parameter(key)
            self.params[key].value = value


def isparametric(obj):

    if callable(obj):
        try:
            obj()
            return False
        except AssertionError:
            return True
        except TypeError:
            return False
    elif hasattr(obj, "__dict__"):
        for elm in obj.__dict__:
            _obj = getattr(obj, elm)
            if hasattr(_obj, "__dict__"):
                for (k, v) in _obj.__dict__.items():
                    if isparametric(v):
                        return True
            elif isinstance(_obj, dict):
                for (k, v) in _obj.items():
                    if isparametric(v):
                        return True
            elif isinstance(_obj, list):
                for elm in _obj:
                    if isparametric(elm):
                        return True
            elif isinstance(_obj, tuple):
                for elm in list(_obj):
                    if isparametric(elm):
                        return True
            else:
                if isparametric(_obj):
                    return True
        return False
    elif isinstance(obj, dict):
        for (k, v) in obj.items():
            if isparametric(v):
                return True
    elif isinstance(obj, str):
        return False
    elif obj is None:
        return False
    elif isinstance(obj, list):
        for elm in obj:
            if isparametric(elm):
                return True
    elif isinstance(obj, tuple):
        for elm in list(obj):
            if isparametric(elm):
                return True
    else:
        return False


def iscallable(obj):
    if callable(obj):
        return True
    elif isinstance(obj, dict):
        for (k, v) in obj.items():
            if iscallable(v):
                return True
        return False
    elif isinstance(obj, list):
        for e in obj:
            if iscallable(e):
                return True
        return False
    elif isinstance(obj, tuple):
        return iscallable(list(obj))
    else:
        return False
