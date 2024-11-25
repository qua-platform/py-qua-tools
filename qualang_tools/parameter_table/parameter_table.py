"""
Parameter Table: Class enabling the mapping of parameters to be updated to their corresponding 
"to-be-declared" QUA variables.

Author: Arthur Strauss - Quantum Machines
Created: 25/11/2024
"""

from typing import Optional, List, Dict, Union, Tuple
import numpy as np
from qm.qua import *
from .parameter_value import ParameterValue

class ParameterTable:
    """
    Class enabling the mapping of parameters to be updated to their corresponding "to-be-declared" QUA variables. The
    type of the QUA variable to be adjusted is automatically inferred from the type of the initial_parameter_value.
    Each parameter in the dictionary should be given a name that the user can then easily access through the table
    with table[parameter_name]. Calling this will return the QUA variable built within the QUA program corresponding
    to the parameter name and its associated Python initial value. Args: parameters_dict: Dictionary of the form {
    "parameter_name": initial_parameter_value }. the QUA program.
    """

    def __init__(
        self,
        parameters_dict: Dict[
            str,
            Union[
                Tuple[Union[float, int, bool, List, np.ndarray], Optional[Union[str,type]], Optional[str]],
                Union[float, int, bool, List, np.ndarray],
            ],
        ],
    ):
        """
        Class enabling the mapping of parameters to be updated to their corresponding "to-be-declared" QUA variables.
        The type of the QUA variable to be adjusted can be specified or either be automatically inferred from the
        type of the initial_parameter_value. Each parameter in the dictionary should be given a name that the user
        can then easily access through the table with table[parameter_name]. Calling this will return the QUA
        variable built within the QUA program corresponding to the parameter name and its associated Python initial
        value. 
        
        Args: parameters_dict: Dictionary should be of the form { "parameter_name": (initial_value,
        qua_type, Literal["input_stream"]) } where qua_type is the type of the QUA variable
        to be declared (int, fixed, bool) and the last (optional) field indicates if the variable
        should be declared as an input_stream instead of a standard QUA variable


        """
        self.parameters_dict = parameters_dict
        self.table = {}
        for index, (parameter_name, parameter_value) in enumerate(self.parameters_dict.items()):
            input_stream = False
            if isinstance(parameter_value, Tuple):
                assert len(parameter_value) <= 3, "Invalid format for parameter value."
                assert isinstance(parameter_value[0], (int, float, bool, List, np.ndarray)), (
                    "Invalid format for parameter value. Please use (initial_value, qua_type) or initial_value."
                )
                if len(parameter_value) >= 2:
                    assert (isinstance(parameter_value[1], (str, type))
                            or parameter_value[1] is None or parameter_value[1] == fixed), (
                        "Invalid format for parameter value. Please use (initial_value, qua_type) or initial_value."
                    )

                if len(parameter_value) == 3:
                    assert parameter_value[2] == "input_stream", (
                        "Invalid format for parameter value. Please use (initial_value, qua_type, input_stream) or initial_value."
                    )
                    if parameter_value[2] == "input_stream":
                        input_stream = True

                self.table[parameter_name] = ParameterValue(
                    parameter_name, parameter_value[0], index, parameter_value[1], input_stream
                )
            else:
                self.table[parameter_name] = ParameterValue(parameter_name, parameter_value, index)

    def declare_variables(self, pause_program=True):
        """
        QUA Macro to declare all QUA variables associated with the parameter table.
        Should be called at the beginning of the QUA program.
        """
        for parameter_name, parameter in self.table.items():
            parameter.declare_variable()
        if pause_program:
            pause()
        if len(self.variables) == 1:
            return self.variables[0]
        else:
            return self.variables

    def assign_parameters(self, values: Dict[Union[str, ParameterValue], Union[int, float, bool, List, np.ndarray, QuaExpressionType]]):
        """
        Assign values to the parameters of the parameter table within the QUA program.
        Args: values: Dictionary of the form { "parameter_name": parameter_value }. The parameter value can be either
        a Python value or a QuaExpressionType.
        """
        for parameter_name, parameter_value in values.items():
            if isinstance(parameter_name, str) and parameter_name not in self.table.keys():
                raise KeyError(f"No parameter named {parameter_name} in the parameter table.")
            if isinstance(parameter_name, str):
                self.table[parameter_name].assign_value(parameter_value)
            else:
                if not isinstance(parameter_name, ParameterValue):
                    raise ValueError("Invalid parameter name. Please use a string or a ParameterValue object.")
                assert parameter_name in self.values, "Provided ParameterValue not in this ParameterTable."
                parameter_name.assign_value(parameter_value)


    def print_parameters(self):
        text = ""
        for parameter_name, parameter in self.table.items():
            text += f"{parameter_name}: {parameter.value}, \n"
        print(text)
    
    def get_type(self, parameter: Union[str, int]):
        """
        Get the type of a specific parameter in the parameter table (specified by name or index).
        
        Args: parameter: Name or index (within current table) of the parameter to get the type of.
        
        Returns: Type of the parameter in the parameter table.
        """
        if isinstance(parameter, str):
            if parameter not in self.table.keys():
                raise KeyError(f"No parameter named {parameter} in the parameter table.")
            return self.table[parameter].type
        elif isinstance(parameter, int):
            for param in self.values:
                if param.index == parameter:
                    return param.type
    
    def get_index(self, parameter_name: str):
        """
        Get the index of a specific parameter in the parameter table.
        Args: parameter_name: Name of the parameter to get the index of.
        Returns: Index of the parameter in the parameter table.
        """
        if parameter_name not in self.table.keys():
            raise KeyError(f"No parameter named {parameter_name} in the parameter table.")
        return self.table[parameter_name].index
    
    
    def get_value(self, parameter: Union[str, int]):
        """
        Get the ParameterValue object of a specific parameter in the parameter table. 
        This object contains the QUA variable corresponding to the parameter, its type, 
        its index within the current table. 
        
        Args: parameter: Name or index (within current table) of the parameter to be returned.
        
        Returns: ParameterValue object corresponding to the specified input.
        """
        if isinstance(parameter, str):
            if parameter not in self.table.keys():
                raise KeyError(f"No parameter named {parameter} in the parameter table.")
            return self.table[parameter]
        elif isinstance(parameter, int):
            for param in self.values:
                if param.index == parameter:
                    return param
    
    def get_variable(self, parameter: Union[str, int]):
        """
        Get the QUA variable corresponding to the specified parameter name.
        
        Args: parameter: Name or index (within current table) of the parameter to be returned.
        Returns: QUA variable corresponding to the parameter name.
        
        """
        if isinstance(parameter, str):
            if parameter not in self.table.keys():
                raise KeyError(f"No parameter named {parameter} in the parameter table.")
            return self.table[parameter].var
        elif isinstance(parameter, int):
            for param in self.values:
                if param.index == parameter:
                    return param.var

    def add_parameter(self, parameter_value: Union[ParameterValue, List[ParameterValue]]):
        """
        Add a (list of) parameter(s) to the parameter table.
        Args: parameter_value: (List of) ParameterValue(s) object(s) to be added to current parameter table.
        """
        if isinstance(parameter_value, List):
            for parameter in parameter_value:
                if parameter.name in self.table.keys():
                    raise KeyError(f"Parameter {parameter.name} already exists in the parameter table.")
                max_index = max([param.index for param in self.values])
                parameter.index = max_index + 1

                self.table[parameter.name] = parameter
        elif isinstance(parameter_value, ParameterValue):
            return self.add_parameter([parameter_value])

    def remove_parameter(self, parameter_value: Union[str, ParameterValue]):
        """
        Remove a parameter from the parameter table.
        Args: parameter_value: Name of the parameter to be removed or ParameterValue object to be removed.
        """
        if isinstance(parameter_value, str):
            if parameter_value not in self.table.keys():
                raise KeyError(f"No parameter named {parameter_value} in the parameter table.")
            del self.table[parameter_value]
        elif isinstance(parameter_value, ParameterValue):
            if parameter_value not in self.values:
                raise KeyError("Provided ParameterValue not in this ParameterTable.")
            del self.table[parameter_value.name]
        else:
            raise ValueError("Invalid parameter name. Please use a string or a ParameterValue object.")

    def add_table(self, parameter_table: Union[List["ParameterTable"], "ParameterTable"]) -> "ParameterTable":
        """
        Add a parameter table to the current table.
        Args: parameter_table: ParameterTable object to be merged with the current table.
        """
        if isinstance(parameter_table, ParameterTable):
            return self.add_table([parameter_table])
        elif isinstance(parameter_table, List):
            for table in parameter_table:
                for parameter in table.table.values():
                    if parameter.name in self.table.keys():
                        raise KeyError(f"Parameter {parameter.name} already exists in the parameter table.")
                    self.table[parameter.name] = parameter

        else:
            raise ValueError("Invalid parameter table. Please use a ParameterTable object "
                             "or a list of ParameterTable objects.")

        return self
    

    def __contains__(self, item):
        return item in self.table.keys()

    def __iter__(self):
        return iter(self.table.keys())

    def __setitem__(self, key, value):
        """
        Assign values to the parameters of the parameter table within the QUA program.
        Args: key: Name of the parameter to be assigned. value: Value to be assigned to the parameter.
        """
        if key not in self.table.keys():
            raise KeyError(f"No parameter named {key} in the parameter table.")
        self.table[key].assign_value(value)


    def __getitem__(self, item: Union[str, int]):
        """
        Returns the QUA variable corresponding to the specified parameter name or parameter index.
        """
        if isinstance(item, str):
            if item not in self.table.keys():
                raise KeyError(f"No parameter named {item} in the parameter table.")
            if self.table[item].is_declared:
                return self.table[item].var
            else:
                raise ValueError(
                    f"No QUA variable found for parameter {item}. Please use "
                    f"ParameterTable.declare_variables() within QUA program first."
                )
        elif isinstance(item, int):
            for parameter in self.table.values():
                if parameter.index == item:
                    if parameter.is_declared:
                        return parameter.var
                    else:
                        raise ValueError(
                            f"No QUA variable found for parameter {item}. Please use "
                            f"ParameterTable.declare_variables() within QUA program first."
                        )
        else:
            raise ValueError("Invalid parameter name. Please use a string or an int.")

    def __len__(self):
        return len(self.table)

    @property
    def variables(self):
        """
        List of the QUA variables corresponding to the parameters in the parameter table.
        """
        
        return [self[item] for item in self.table.keys()]
        
    
    @property
    def variables_dict(self):
        """Dictionary of the QUA variables corresponding to the parameters in the parameter table."""
        if not self.is_declared:
            raise ValueError("Not all parameters have been declared. Please declare all parameters first.")
        return {parameter_name: parameter.var for parameter_name, parameter in self.table.items()}

    @property
    def values(self):
        """
        List of the parameter values objects in the parameter table.
        
        Returns: List of ParameterValue objects in the parameter table.
        """
        return list(self.table.values())
    
    
    @property
    def is_declared(self):
        """Boolean indicating if all the QUA variables have been declared."""
        return all(parameter.is_declared for parameter in self.values)

    def __repr__(self):
        text = ""
        for parameter in self.table.values():
            text += parameter.__repr__()
        return text
