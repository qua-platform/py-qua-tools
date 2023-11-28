import threading

from qm.qua import *
from qm import QuantumMachine, QmJob, Program
import time
from typing import Optional, List, Dict
from dataclasses import dataclass


@dataclass
class ParameterTable:
    """
    Data class enabling the mapping of parameters to be updated to their corresponding "to-be-declared" QUA variables.
    The type of the QUA variable to be adjusted is automatically inferred from the type of the initial_parameter_value.
    Each parameter in the dictionary should be given a name that the user can then easily access through the table with
    table[parameter_name]. Calling this will return the QUA variable built within the QUA program corresponding to the parameter name
    and its associated Python initial value.
    Args:
        parameters_dict: Dictionary of the form { "parameter_name": initial_parameter_value }.

    """
    parameters_dict: Dict[str, float | int | bool]

    def __post_init__(self):
        self.table = {}
        for index, (parameter_name, parameter_value) in enumerate(self.parameters_dict.items()):
            self.table[parameter_name] = {"index": index}
            if isinstance(parameter_value, float):
                if float(parameter_value).is_integer() and parameter_value > 8:
                    self.table[parameter_name]["declare_expression"] = f'declare(int, value=int({parameter_value}))'
                    self.table[parameter_name]["type"] = int
                    self.table[parameter_name]["value"] = parameter_value
                else:
                    self.table[parameter_name]["declare_expression"] = f'declare(fixed, value={parameter_value})'
                    self.table[parameter_name]["type"] = float
                    self.table[parameter_name]["value"] = parameter_value

                self.table[parameter_name]["length"] = 0

            elif isinstance(parameter_value, int):
                self.table[parameter_name]["declare_expression"] = f'declare(int, value={parameter_value})'
                self.table[parameter_name]["type"] = int
                self.table[parameter_name]["length"] = 0
                self.table[parameter_name]["value"] = parameter_value

            elif isinstance(parameter_value, bool):
                self.table[parameter_name]["declare_expression"] = f'declare(bool, value={parameter_value})'
                self.table[parameter_name]["type"] = bool
                self.table[parameter_name]["length"] = 0
                self.table[parameter_name]["value"] = parameter_value

            elif isinstance(parameter_value, (List, np.ndarray)):
                if isinstance(parameter_value, np.ndarray):
                    assert parameter_value.ndim == 1, "Invalid parameter type, array must be 1D."
                    parameter_value = parameter_value.tolist()
                assert all(isinstance(x, type(parameter_value[0])) for x in
                           parameter_value), "Invalid parameter type, all elements must be of same type."
                if isinstance(parameter_value[0], bool):
                    self.table[parameter_name]["declare_expression"] = f'declare(bool, value={parameter_value})'
                if isinstance(parameter_value[0], int):
                    self.table[parameter_name]["declare_expression"] = f'declare(int, value={parameter_value})'
                elif isinstance(parameter_value[0], float):
                    self.table[parameter_name]["declare_expression"] = f'declare(fixed, value={parameter_value})'
                self.table[parameter_name]["type"] = List
                self.table[parameter_name]["length"] = len(parameter_value)
            else:
                raise ValueError("Invalid parameter type. Please use float, int or bool or list.")

    def declare_variables(self):
        """
        QUA Macro to create the QUA variables associated with the parameter table.
        """
        for parameter_name, parameter in self.table.items():
            if parameter["declare_expression"] is not None:
                print(f"{parameter_name} = {parameter['declare_expression']}")
                exec(f"{parameter_name} = {parameter['declare_expression']}")
                self.table[parameter_name]["var"] = eval(parameter_name)

    def load_parameters(self, pause_program=False):
        """ QUA Macro to be called within QUA program to retrieve updated values for the parameters through IO 1 and IO 2.
        Args:
            pause_program: Boolean indicating whether the program should be paused while waiting for user input.
        """

        if pause_program:
            pause()
        param_index_var = declare(int)
        assign(param_index_var, IO1)

        with switch_(param_index_var):
            for parameter in self.table.values():
                with case_(parameter["index"]):
                    if parameter["length"] == 0:
                        assign(parameter["var"], IO2)
                    else:
                        looping_var = declare(int)
                        with for_(looping_var, 0, looping_var < parameter["var"].length(), looping_var + 1):
                            pause()
                            assign(parameter["var"][looping_var], IO2)

            with default_():
                pass


    def get_parameters(self):
        text = ""
        for parameter_name, parameter in self.table.items():
            text += f"{parameter_name}: {parameter['value']}, "
        print(text)
    def __getitem__(self, item):
        return self.table[item]["var"]

    @property
    def variables(self):
        return [var["var"] for var in self.table.values() if var["declare_expression"] is not None]


class VideoMode:
    def __init__(self, qm: QuantumMachine, parameters: Dict | ParameterTable, job: QmJob = None):  # TODO: optional[QmJob] returns an error
        """
        This class aims to provide an easy way to update parameters in a QUA program through user input while the
        program is running. It is particularly useful for calibrating parameters in real time. The user can specify the
        parameters to be updated and their initial values in the parameters dictionary. The video mode will then
        automatically create the corresponding QUA variables and update them through user input.

        The way this is done is by adding two methods of this class at the beginning of the QUA program declaration:

        - ```declare_variables```: This method will create the QUA variables corresponding to the parameters to be updated.
        - ```load_parameters```: This method will load the updated values for the parameters through IO 1 and IO 2.
        The user can then start the video mode outside the QUA program by calling the ```start``` method of this class.
        This will start a new parallel thread in charge of updating the parameters in the parameter table through user input.
        The user can stop the video mode by entering 'stop' in the terminal.
        The user can also resume a paused program by entering 'done' again in the terminal.

        Args:
            qm: Quantum Machine object.
            parameters: Parameter table containing the parameters to be updated and their initial values.
            job: QM job already executed. If None, the video mode will start the execution of the QUA program through the start method
            of this class.
        """
        self.qm = qm
        self.job = job
        self._parameter_table = parameters if isinstance(parameters, ParameterTable) else ParameterTable(parameters)
        self.active = True
        self.thread = threading.Thread(target=self.update_parameters)
        # self.thread.start()

    def update_parameters(self):
        """Update parameters in the parameter table through user input.

        """
        while self.active:

            param_name = input("Enter parameter name (or 'stop' to quit VideoMode or 'done' to resume program): ")

            if param_name == 'stop':
                self.active = False
                break

            elif param_name == 'done' and self.job is not None:
                if self.job.is_paused():
                    self.job.resume()
                self.job.halt()

            elif param_name in self.parameter_table.table.keys():
                self.qm.set_io1_value(self.parameter_table.table[param_name]["index"])
                param_value = input("Enter parameter value (if list: enter each value separated by a space): ")

                if self.parameter_table.table[param_name]["type"] == List:
                    param_value = param_value.split()
                    if len(param_value) != self.parameter_table.table[param_name]["length"]:
                        print(f"Invalid input. {self.parameter_table[param_name]} should be a list of length "
                              f"{self.parameter_table.table[param_name]['length']}.")
                    elif param_value[0].isnumeric():
                        try:
                            param_value = list(map(int, param_value))
                        except ValueError:
                            print("One of the values could not be cast to int ("
                                  "casting done according to type of first value): ")
                    elif param_value[0].replace('.', '', 1).isdigit():
                        try:
                            param_value = list(map(float, param_value))
                        except ValueError:
                            print("One of the values could not be cast to float ("
                                  "casting done based on type of first value): ")
                    elif param_value[0] in ['True', 'False']:
                        try:
                            param_value = list(map(bool, param_value))
                        except ValueError:
                            print("One of the values could not be cast to bool (casting done based on type of "
                                  "first value): ")

                    assert all(isinstance(x, type(param_value[0])) for x in
                               param_value), f"Invalid input. {self.parameter_table[param_name]} should be a list of elements of the same type."

                    for value in param_value:
                        while not (self.job.is_paused()):
                            time.sleep(0.001)
                        self.qm.set_io2_value(value)
                        self.parameter_table.table[param_name]["value"] = value
                        self.job.resume()

                else:
                    if self.parameter_table.table[param_name]["type"] == int:
                        if not param_value.isnumeric():
                            print(f"Invalid input. {self.parameter_table[param_name]} should be an integer.")
                        else:
                            try:
                                param_value = int(param_value)
                            except ValueError:
                                print(f"Invalid input. {self.parameter_table[param_name]} could not be "
                                      f"converted to int.")
                                continue

                    elif self.parameter_table.table[param_name]["type"] == float:
                        try:
                            param_value = float(param_value)
                        except ValueError:
                            print(f"Invalid input. {self.parameter_table[param_name]} should be a float.")
                            continue

                    elif self.parameter_table.table[param_name]["type"] == bool:
                        if param_value not in ['True', 'False', '0', '1']:
                            print(f"Invalid input. {self.parameter_table[param_name]} should be a boolean.")
                        elif param_value in ['0', '1']:
                            param_value = bool(int(param_value))
                        else:
                            try:
                                param_value = bool(param_value)
                            except ValueError:
                                print(f"Invalid input. {self.parameter_table[param_name]} could not be cast to bool")
                    self.qm.set_io2_value(param_value)
                    self.parameter_table.table[param_name]["value"] = param_value
            elif param_name == 'get':
                self.parameter_table.get_parameters()
            else:
                print(f"Invalid input. {param_name} is not a valid parameter name.")

        print("VideoMode stopped.")

    def start(self, prog: Optional[Program] = None, *execute_args) -> None:
        """Start the video mode.
        Args:
            prog: QUA program to be executed. If None, the video mode will be started without executing a QUA program
            (program assumed to be running)
            execute_args: Arguments to be passed to the execute method of the QuantumMachine for executing the program.
            """
        if self.job is None:
            self.job = self.qm.execute(prog, *execute_args)
        print("start")
        self.thread.start()

    @property
    def parameter_table(self):
        return self._parameter_table

    @property
    def variables(self):
        return self.parameter_table.variables

    def load_parameters(self, pause_program=False):

        self.parameter_table.load_parameters(pause_program)

    def declare_variables(self):
        self.parameter_table.declare_variables()

    def __getitem__(self, item):
        return self._parameter_table[item]
