"""
This module provides the ParameterValue class, which enables the mapping of a parameter to a QUA variable to be updated.

Author: Arthur Strauss - Quantum Machines
Created: 25/11/2024
"""

from typing import Optional, List, Dict, Union, Tuple
import numpy as np
from qm.qua import *

def set_type(qua_type: Union[str, type]):
    """
    Set the type of the QUA variable to be declared.
    Args: qua_type: Type of the QUA variable to be declared (int, fixed, bool).
    """

    if qua_type == "fixed" or qua_type == fixed:
        return fixed
    elif qua_type == "bool" or qua_type == bool:
        return bool
    elif qua_type == "int" or qua_type == int:
        return int
    else:
        raise ValueError("Invalid QUA type. Please use 'fixed', 'int' or 'bool'.")


def infer_type(value: Union[int, float, List, np.ndarray] = None):
    """
    Infer automatically the type of the QUA variable to be declared from the type of the initial parameter value.
    """
    if isinstance(value, float):
        if value.is_integer() and value > 8:
            return int
        else:
            return fixed

    elif isinstance(value, bool):
        return bool

    elif isinstance(value, int):
        return int

    elif isinstance(value, (List, np.ndarray)):
        if isinstance(value, np.ndarray):
            assert value.ndim == 1, "Invalid parameter type, array must be 1D."
            value = value.tolist()
        assert all(
            isinstance(x, type(value[0])) for x in value
        ), "Invalid parameter type, all elements must be of same type."
        if isinstance(value[0], bool):
            return bool
        elif isinstance(value[0], int):
            return int
        elif isinstance(value[0], float):
            return fixed
    else:
        raise ValueError("Invalid parameter type. Please use float, int or bool or list.")


class ParameterValue:
    """
    Class enabling the mapping of a parameter to a QUA variable to be updated. The type of the QUA variable to be
    adjusted can be declared explicitly or either be automatically inferred from the type of provided initial value.
    """

    def __init__(
        self,
        name: str,
        value: Union[int, float, List, np.ndarray],
        index: int = 0,
        qua_type: Optional[Union[str, type]] = None,
        input_stream: Optional[bool] = False,
    ):
        """

        Args:
            name: Name of the parameter.
            value: Initial value of the parameter.
            index: Index of the parameter in the parameter table.
            qua_type: Type of the QUA variable to be declared (int, fixed, bool). Default is None.
            input_stream: Boolean indicating if the variable should be declared as an input_stream instead of a standard
                QUA variable. Default is False.
        """
        self._name = name
        self.value = value
        self._index = index
        self.var = None
        self._type = set_type(qua_type) if qua_type is not None else infer_type(value)
        self._length = 0 if not isinstance(value, (List, np.ndarray)) else len(value)
        self._input_stream = input_stream
        self._is_declared = False

    def __repr__(self):
        return f"{self.name}: ({self.value}, {self.type}) \n"

    def assign_value(self, value: Union["ParameterValue", float, int, bool, 
    List[Union[float, int, bool, QuaVariableType]],
    QuaVariableType], is_qua_array: bool = False):
        """
        Assign value to the QUA variable corresponding to the parameter.
        Args: value: Value to be assigned to the QUA variable. If the ParameterValue corresponds to a QUA array,
            the value should be a list or a QUA array of the same length.
        is_qua_array: Boolean indicating if provided value is a QUA array (True) or a list of values (False).
            Default is False.
            If True, the value should be a QUA array of the same length as the parameter. When assigning a QUA array,
            a QUA loop is created to assign each element of the array to the corresponding element of the QUA array.
            If False, a Python loop is used instead.
        """
        if isinstance(value, ParameterValue):
            self.var = value.var
            self.value = value.value
            self._type = value.type
            self._length = value.length
            self._input_stream = value.input_stream
            self._is_declared = value.is_declared
            return
        if self.length == 0:
            if isinstance(value, List):
                raise ValueError(f"Invalid input. {self.name} should be a single value, not a list.")
            assign(self.var, value)
        else:
            if is_qua_array:
                iterator = declare(int)
                with for_(iterator, 0, iterator < self.length, iterator + 1):
                    assign(self.var[iterator], value[iterator])
            else:
                if len(value) != self.length:
                    raise ValueError(
                        f"Invalid input. {self.name} should be a list of length {self.length}."
                    )
                for i in range(self.length):
                    assign(self.var[i], value[i])

    def declare_variable(self, pause_program=False):
        """
        Declare the QUA variable associated with the parameter.
        """
        if self.input_stream:
            self.var = declare_input_stream(t=self.type, name=self.name, value=self.value)
        else:
            self.var = declare(t=self.type, value=self.value)
        if pause_program:
            pause()
        self._is_declared = True
        return self.var

    @property
    def is_declared(self):
        """Boolean indicating if the QUA variable has been declared."""
        return self._is_declared
    
    @property
    def name(self):
        """Name of the parameter."""
        return self._name
    
    @property
    def index(self):
        """Index of the parameter in the parameter table."""
        return self._index
    
    @index.setter
    def index(self, value: int):
        if value < 0:
            raise ValueError("Index must be a positive integer.")
        self._index = value
    
    @property
    def type(self):
        """Type of the associated QUA variable."""
        return self._type
    
    @property
    def length(self):
        """Length of the parameter if it refers to a QUA array (
        returns 0 if single value)."""
        return self._length
    
    @property
    def input_stream(self):
        """Boolean indicating if the QUA variable is an input stream."""
        return self._input_stream