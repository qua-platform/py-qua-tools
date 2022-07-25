import warnings
import re


class ConfigurationError(Exception):
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)


def _warn_if_not_none(kwargs, deprecated_arg):
    suggested_arg = "element_" + re.split("_ports", deprecated_arg)[0] + "s"
    val = kwargs.get(deprecated_arg, None)
    if val is not None:
        warnings.warn(
            "{0} is deprecated use {1}".format(deprecated_arg, suggested_arg),
            DeprecationWarning,
        )
    return val
