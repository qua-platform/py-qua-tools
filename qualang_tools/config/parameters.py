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


def _is_parametric(obj):
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
                    if _is_parametric(v):
                        return True
            elif isinstance(_obj, dict):
                for (k, v) in _obj.items():
                    if _is_parametric(v):
                        return True
            elif isinstance(_obj, list):
                for elm in _obj:
                    if _is_parametric(elm):
                        return True
            elif isinstance(_obj, tuple):
                for elm in list(_obj):
                    if _is_parametric(elm):
                        return True
            else:
                if _is_parametric(_obj):
                    return True
        return False
    elif isinstance(obj, dict):
        for (k, v) in obj.items():
            if _is_parametric(v):
                return True
    elif isinstance(obj, str):
        return False
    elif obj is None:
        return False
    elif isinstance(obj, list):
        for elm in obj:
            if _is_parametric(elm):
                return True
    elif isinstance(obj, tuple):
        for elm in list(obj):
            if _is_parametric(elm):
                return True
    else:
        return False


def _is_callable(obj):
    if callable(obj):
        return True
    elif isinstance(obj, dict):
        for (k, v) in obj.items():
            if _is_callable(v):
                return True
        return False
    elif isinstance(obj, list):
        for e in obj:
            if _is_callable(e):
                return True
        return False
    elif isinstance(obj, tuple):
        return _is_callable(list(obj))
    else:
        return False
