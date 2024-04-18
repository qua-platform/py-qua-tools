# VideoMode script enabling the update of parameters in a QUA program through user input while the program is running.
# Authors: Arthur Strauss, Théo Laudat
# Date: 19/12/2023

import threading
from qm.qua import *
from qm import QuantumMachine, QmJob, Program
import time
import signal
from typing import Optional, List, Dict, Union, Tuple
import numpy as np


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
    def __init__(
        self,
        name: str,
        value: Union[int, float, List, np.ndarray],
        index: int,
        qua_type: Optional[Union[str, type]] = None,
    ):
        """ """
        self.name = name
        self.value = value
        self.index = index
        self.var = None
        self.type = set_type(qua_type) if qua_type is not None else infer_type(value)
        self.length = 0 if not isinstance(value, (List, np.ndarray)) else len(value)

    def __repr__(self):
        return f"{self.name}: ({self.value}, {self.type}) \n"


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
                Tuple[Union[float, int, bool, List, np.ndarray], Optional[str]],
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
        value. Args: parameters_dict: Dictionary should be of the form { "parameter_name": (initial_value,
        qua_type) } where qua_type is the type of the QUA variable to be declared (int, fixed, bool).


        """
        self.parameters_dict = parameters_dict
        self.table = {}
        for index, (parameter_name, parameter_value) in enumerate(self.parameters_dict.items()):
            if isinstance(parameter_value, Tuple):
                if len(parameter_value) != 2:
                    raise ValueError(
                        "Invalid format for parameter value. Please use (initial_value, qua_type) or initial_value."
                    )
                self.table[parameter_name] = ParameterValue(
                    parameter_name, parameter_value[0], index, parameter_value[1]
                )
            else:
                self.table[parameter_name] = ParameterValue(parameter_name, parameter_value, index)

    def declare_variables(self):
        """
        QUA Macro to create the QUA variables associated with the parameter table.
        """
        for parameter_name, parameter in self.table.items():
            parameter.var = declare(t=parameter.type, value=parameter.value)
        pause()
        if len(self.variables) == 1:
            return self.variables[0]
        else:
            return self.variables

    def load_parameters(self, pause_program=False):
        """QUA Macro to be called within QUA program to retrieve updated values for the parameters through IO 1 and IO2.
        Args:
            pause_program: Boolean indicating whether the program should be paused while waiting for user input.
        """

        if pause_program:
            pause()

        param_index_var = declare(int)
        assign(param_index_var, IO1)

        with switch_(param_index_var):
            for parameter in self.table.values():
                with case_(parameter.index):
                    if parameter.length == 0:
                        assign(parameter.var, IO2)
                    else:
                        looping_var = declare(int)
                        with for_(
                            looping_var,
                            0,
                            looping_var < parameter.var.length(),
                            looping_var + 1,
                        ):
                            pause()
                            assign(parameter.var[looping_var], IO2)

            with default_():
                pass

    def print_parameters(self):
        text = ""
        for parameter_name, parameter in self.table.items():
            text += f"{parameter_name}: {parameter.value}, \n"
        print(text)

    def get_parameters(self):
        """
        Get dictionary of all parameters with latest updated values
        Args: parameter_name: Name of the parameter to be returned. If None, all parameters are printed.
        Returns: if parameter_name is None, Dictionary of the form { "parameter_name": parameter_value },
                else parameter_value associated to parameter_name.
        """
        return {parameter_name: parameter.value for parameter_name, parameter in self.table.items()}

    def get_parameter(self, param_name: str):
        """
        Get the value of a specific arameter with latest updated value
        Args: parameter_name: Name of the parameter to be returned. If None, all parameters are printed.
        Returns: if parameter_name is None, Dictionary of the form { "parameter_name": parameter_value },
                else parameter_value associated to parameter_name.
        """
        if param_name not in self.table.keys():
            raise KeyError(f"No parameter named {param_name} in the parameter table.")
        return self.table[param_name].value

    def __getitem__(self, item):
        """
        Returns the QUA variable corresponding to the parameter name.
        """

        if self.table[item].var is not None:
            return self.table[item].var
        else:
            raise ValueError(
                f"No QUA variable found for parameter {item}. Please use "
                f"VideoMode.declare_variables() within QUA program first."
            )

    @property
    def variables(self):
        """List of the QUA variables corresponding to the parameters in the parameter table."""
        try:
            return [self[item] for item in self.table.keys()]
        except KeyError:
            raise KeyError(
                "No QUA variables found for parameters. Please use "
                "VideoMode.declare_variables() within QUA program first."
            )

    def __repr__(self):
        text = ""
        for parameter in self.table.values():
            text += parameter.__repr__()
        return text


class VideoMode:
    """
    This class aims to provide an easy way to update parameters in a QUA program through user input while the
    program is running. It is particularly useful for calibrating parameters dynamically and without deterministic
    of the parameters values. The user can specify
    the parameters to be updated and their initial values in the parameter dictionary called ```param_dict```.
    """

    _default_io1 = 2**31 - 1
    _default_io2 = 0.0

    def __init__(self, qm: QuantumMachine, parameters: Union[Dict, ParameterTable]):
        """
        This class aims to provide an easy way to update parameters in a QUA program through user input while the
        program is running. It is particularly useful for calibrating parameters in real time. The user can specify
        the parameters to be updated and their initial values in the parameter dictionary called ```param_dict```.
        The video mode will then automatically create the corresponding QUA variables and update them through user
        input.

        Parameters dictionary should be of the form:
         ```{"parameter_name": (initial_parameter_value, qua_type) }```
            where ```qua_type``` is the type of the QUA variable to be declared (int, fixed, bool).

        The way this is done is by adding two methods of this class at the beginning of the QUA program declaration:

        - ```declare_variables```: This method will create the QUA variables corresponding to the parameters to be updated.
        - ```load_parameters```: This method will load the updated values for the parameters through IO variables  1 and 2.

        The user can then start the video mode outside the QUA program by calling the ```execute``` method of this class.
        This will start a new parallel thread in charge of updating the
        parameters in the parameter table through user input. The user can stop the video mode by entering 'stop' in
        the terminal. The user can also resume a paused program by entering 'done' again in the terminal.

        Args:
            qm: Quantum Machine object.
            parameters: Dictionary or ParameterTable containing the parameters to be updated and their initial values and types.
        """
        self.qm = qm
        self.job = None
        self._parameter_table = parameters if isinstance(parameters, ParameterTable) else ParameterTable(parameters)
        self.active = True
        self.thread = threading.Thread(target=self.update_parameters)
        self.stop_event = threading.Event()
        self.implemented_commands = (
            "List of implemented commands: \n "
            "get: return the current value of the parameters. \n "
            "stop: quit VideoMode. \n "
            "done: resume program (if pause_program==True). \n "
            "help: display the list of available commands. \n "
            "'param_name'='param_value': set the parameter to the specified value (ex: V1=0.152).\n "
            "'param_name': return the value of the parameter.\n"
        )

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Signal handler for SIGTERM and SIGINT signals."""
        print(f"Received signal {signum}, stopping VideoMode...")
        self.qm.set_io1_value(self._default_io1)
        self.qm.set_io2_value(self._default_io2)
        self.job.halt()
        self.stop_event.set()
        # For shutting down the entire program
        # sys.exit(0)

    def update_parameters(self):
        """Update parameters in the parameter table through user input."""
        while not self.stop_event.is_set() and self.active:
            param_name = input("Enter a command (type help for getting the list of available commands): ")
            messages = param_name.split("=")
            if len(messages) == 1:
                if messages[0] == "stop":
                    self.active = False
                    self.job.halt()
                    break

                elif messages[0] == "done" and self.job is not None:
                    if self.job.is_paused():
                        self.job.resume()

                elif messages[0] == "get":
                    self.parameter_table.print_parameters()

                elif messages[0] == "help":
                    print(self.implemented_commands)

                elif messages[0] in self.parameter_table.table.keys():
                    print(self.parameter_table.table[messages[0]].value)

                else:
                    print(f"Invalid input. {messages[0]} is not a valid command.")

            elif len(messages) == 2:
                param_name = messages[0]
                param_value = messages[1]
                if param_name in self.parameter_table.table.keys():
                    self.qm.set_io1_value(self.parameter_table.table[param_name].index)

                    if isinstance(self.parameter_table.table[param_name].value, list):
                        param_value = param_value.split()
                        if len(param_value) != self.parameter_table.table[param_name].length:
                            print(
                                f"Invalid input. {self.parameter_table[param_name]} should be a list of length "
                                f"{self.parameter_table.table[param_name].length}."
                            )
                        elif param_value[0].isnumeric():
                            try:
                                param_value = list(map(int, param_value))
                            except ValueError:
                                print(
                                    "One of the values could not be cast to int ("
                                    "casting done according to type of first value): "
                                )
                        elif param_value[0].replace(".", "", 1).isdigit():
                            try:
                                param_value = list(map(float, param_value))
                            except ValueError:
                                print(
                                    "One of the values could not be cast to float ("
                                    "casting done based on type of first value): "
                                )
                        elif param_value[0] in ["True", "False"]:
                            try:
                                param_value = list(map(bool, param_value))
                            except ValueError:
                                print(
                                    "One of the values could not be cast to bool (casting done based on type of "
                                    "first value): "
                                )

                        assert all(isinstance(x, type(param_value[0])) for x in param_value), (
                            f"Invalid input. {self.parameter_table[param_name]} should be a list of elements of the "
                            f"same type."
                        )

                        if self.job.is_paused():
                            # If the program is paused before param loading,
                            # update the parameters directly (no wait through done)
                            self.job.resume()
                        for value in param_value:
                            while not (self.job.is_paused()):
                                time.sleep(0.001)
                            self.qm.set_io2_value(value)
                            self.parameter_table.table[param_name].value = value
                            self.job.resume()

                    else:
                        if self.parameter_table.table[param_name].type == int:
                            if not param_value.isnumeric():
                                print(f"Invalid input. {self.parameter_table[param_name]} should be an integer.")
                            else:
                                try:
                                    param_value = int(param_value)
                                except ValueError:
                                    print(
                                        f"Invalid input. {self.parameter_table[param_name]} could not be "
                                        f"converted to int."
                                    )
                                    continue

                        elif self.parameter_table.table[param_name].type == fixed:
                            try:
                                param_value = float(param_value)
                            except ValueError:
                                print(f"Invalid input. {self.parameter_table[param_name]} should be a float.")
                                continue

                        elif self.parameter_table.table[param_name].type == bool:
                            if param_value not in ["True", "False", "0", "1"]:
                                print(f"Invalid input. {self.parameter_table[param_name]} should be a boolean.")
                            elif param_value in ["0", "1"]:
                                param_value = bool(int(param_value))
                            else:
                                try:
                                    param_value = bool(param_value)
                                except ValueError:
                                    print(
                                        f"Invalid input. {self.parameter_table[param_name]} could not be cast to bool"
                                    )
                        else:
                            print(f"Invalid input. {param_value} is not a valid parameter value.")

                        self.qm.set_io2_value(param_value)
                        self.parameter_table.table[param_name].value = param_value

                else:
                    print(f"Invalid input. {param_name} is not a valid parameter name.")

        print("VideoMode stopped.")

    def execute(self, prog: Optional[Program] = None, *execute_args) -> QmJob:
        """Start the video mode.
        Args:
            prog: QUA program to be executed. If None, the video mode will be started without executing a QUA program
            (program assumed to be running)
            execute_args: Arguments to be passed to the execute method of the QuantumMachine for executing the program.
        Returns:
            the QM job

        """
        if self.job is None:
            self.job = self.qm.execute(prog, *execute_args)
            # Reinitialize the IO values
            self.qm.set_io1_value(666)
            self.qm.set_io2_value(0.0)
            time.sleep(1)
            self.job.resume()
        print("start")
        print(self.implemented_commands)
        self.parameter_table.get_parameters()
        self.thread.start()

        return self.job

    @property
    def parameter_table(self):
        """
        ParameterTable containing the parameters to be updated and their initial values.
        """
        return self._parameter_table

    @property
    def variables(self):
        """List of the QUA variables corresponding to the parameters in the parameter table."""
        return self.parameter_table.variables

    def get_parameters(self):
        """
        Get dictionary of parameters with latest updated values
        Returns: Dictionary of the form { "parameter_name": parameter_value }.
        """
        return self.parameter_table.get_parameters()

    def get_parameter(self, param_name: Optional[str] = None):
        """
        Get the value of a parameter with latest updated values
        """
        return self.parameter_table.get_parameter(param_name)

    def load_parameters(self, pause_program=False):
        """
        QUA Macro to be called within QUA program to retrieve updated values for the parameters through IO 1 and IO2.
        Args:
        pause_program: Boolean indicating whether the program should be paused while waiting for user input.
        """
        self.parameter_table.load_parameters(pause_program)

    def declare_variables(self):
        """
        QUA Macro to create the QUA variables associated with the parameter table.
        :returns : The list of declared QUA variables or the declared variable if there is only one item.
        """
        return self.parameter_table.declare_variables()

    def __getitem__(self, item):
        """
        Returns the QUA variable corresponding to the parameter name.
        """
        return self._parameter_table[item]
