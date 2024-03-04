algebra_supported_types = (int, float)


class Parameter(object):
    def __init__(self, name: str):
        """An object to represents a simple parameter or any setter.
        :param name: Name of the parameter
        :type name: str
        """
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
        """Returns the value of the parameter"""
        return self._value

    @value.setter
    def value(self, v):
        self.is_set = True
        self._value = v

    @property
    def len(self):
        """Returns a new parameter with a value equal to the length of the current parameter."""
        len_self = Parameter("len_" + self.name)

        def func():
            if self.is_set:
                if callable(self._value):
                    return len(self._value())
                else:
                    return len(self._value)
            else:
                raise AssertionError("Parameter {} is not set".format(self.name))

        len_self._value = func
        len_self.is_set = True
        return len_self

    def __add__(self, other):
        if isinstance(other, Parameter):
            new_param = Parameter("add_" + self.name + "_" + other.name)

            def func():
                if self.is_set and other.is_set:
                    return self() + other()
                elif not self.is_set:
                    raise AssertionError("Parameter {} is not set".format(self.name))
                elif not other.is_set:
                    raise AssertionError("Parameter {} is not set".format(other.name))

            new_param._value = func
            new_param.is_set = True
            return new_param
        elif isinstance(other, algebra_supported_types):
            new_param = Parameter("add_" + self.name + "_" + str(other))

            def func():
                if self.is_set:
                    return self() + other
                elif not self.is_set:
                    raise AssertionError("Parameter {} is not set".format(self.name))

            new_param._value = func
            new_param.is_set = True
            return new_param

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, Parameter):
            new_param = Parameter("sub_ " + self.name + "_" + other.name)

            def func():
                if self.is_set and other.is_set:
                    return self() - other()
                elif not self.is_set:
                    raise AssertionError("Parameter {} is not set".format(self.name))
                elif not other.is_set:
                    raise AssertionError("Parameter {} is not set".format(other.name))

            new_param._value = func
            new_param.is_set = True
            return new_param
        elif isinstance(other, algebra_supported_types):
            new_param = Parameter("sub_" + self.name + "_" + str(other))

            def func():
                if self.is_set:
                    return self() - other
                elif not self.is_set:
                    raise AssertionError("Parameter {} is not set".format(self.name))

            new_param._value = func
            new_param.is_set = True
            return new_param

    def __rsub__(self, other):
        return self.__sub__(other)

    def __mul__(self, other):
        if isinstance(other, Parameter):
            new_param = Parameter("mul_ " + self.name + "_" + other.name)

            def func():
                if self.is_set and other.is_set:
                    return self() * other()
                elif not self.is_set:
                    raise AssertionError("Parameter {} is not set".format(self.name))
                elif not other.is_set:
                    raise AssertionError("Parameter {} is not set".format(other.name))

            new_param._value = func
            new_param.is_set = True
            return new_param
        elif isinstance(other, algebra_supported_types):
            new_param = Parameter("mul_" + self.name + "_" + str(other))

            def func():
                if self.is_set:
                    return self() * other
                elif not self.is_set:
                    raise AssertionError("Parameter {} is not set".format(self.name))

            new_param._value = func
            new_param.is_set = True
            return new_param

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, Parameter):
            new_param = Parameter("div_ " + self.name + "_" + other.name)

            def func():
                if self.is_set and other.is_set:
                    return self() / other()
                elif not self.is_set:
                    raise AssertionError("Parameter {} is not set".format(self.name))
                elif not other.is_set:
                    raise AssertionError("Parameter {} is not set".format(other.name))

            new_param._value = func
            new_param.is_set = True
            return new_param
        elif isinstance(other, algebra_supported_types):
            new_param = Parameter("div_" + self.name + "_" + str(other))

            def func():
                if self.is_set:
                    return self() / other
                elif not self.is_set:
                    raise AssertionError("Parameter {} is not set".format(self.name))

            new_param._value = func
            new_param.is_set = True
            return new_param

    def __rtruediv__(self, other):
        return self.__truediv__(other)

    def __pow__(self, other):
        if isinstance(other, Parameter):
            new_param = Parameter("pow_ " + self.name + "_" + other.name)

            def func():
                if self.is_set and other.is_set:
                    return self() ** other()
                elif not self.is_set:
                    raise AssertionError("Parameter {} is not set".format(self.name))
                elif not other.is_set:
                    raise AssertionError("Parameter {} is not set".format(other.name))

            new_param._value = func
            new_param.is_set = True
            return new_param
        elif isinstance(other, algebra_supported_types):
            new_param = Parameter("pow_" + self.name + "_" + str(other))

            def func():
                if self.is_set:
                    return self() ** other
                elif not self.is_set:
                    raise AssertionError("Parameter {} is not set".format(self.name))

            new_param._value = func
            new_param.is_set = True
            return new_param

    def __rpow__(self, other):
        return self.__pow__(other)


class ConfigVars(object):
    def __init__(self):
        """An object that holds a collection of Parameters. Useful to write parametric
        QUA configurations.
        """
        self.params = {}

    def parameter(self, name: str, setter=None):
        """Returns a Parameter with the given name
        :param name: Name of the parameter
        :type name: str
        :param setter: any function
        :type setter: Callable
        """
        if name.find(" ") != -1:
            raise ValueError("Parameter name cannot contain spaces. " "Use underscore of camelCase.")
        if name not in self.params.keys():
            self.params[name] = Parameter(name)
        if setter is not None:
            self.params[name].value = setter
        return self.params[name]

    def set(self, **kwargs):
        """sets the parameters with the given values specified as a dictionary"""
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
                for k, v in _obj.__dict__.items():
                    if _is_parametric(v):
                        return True
            elif isinstance(_obj, dict):
                for k, v in _obj.items():
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
        for k, v in obj.items():
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
    return False


def _is_callable(obj):
    if callable(obj):
        return True
    elif isinstance(obj, dict):
        for k, v in obj.items():
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
    return False
