"""
Jobs for this file

1. Connect to a QM
2. run a reset program
3. format the data using the data handler
4. put the data into the gui
5. run the gui

"""

from qm.QuantumMachinesManager import QuantumMachinesManager
from configuration import *

from IQ_blobs import generate_reset_program, run_and_format
from qualang_tools.plot import launch_reset_gui
from qm.simulate.credentials import create_credentials


def compare_reset(reset_dictionary):
    """
    Compares the results of multiple reset paradigms with a GUI to visualise the differences.

    @param reset_dictionary: A dictionary with format:

    {
        [name of cooldown method (str)]: {'macro': [name of macro function from macros (str)] ,
         'settings': [dictionary of keyword arguments for the macro function (dict)]},
    }

    eg:
    {
        'Cooldown': {'macro': 'cooldown', 'settings': {'cooldown_time': 8}},
        'Active threshold 1': {'macro': 'active', 'settings': {'threshold': -0.003, 'max_tries': 3}},
        'Active threshold 2': {'macro': 'active', 'settings': {'threshold': -0.005, 'max_tries': 5}}
    }


    @return: results dictionary of format {name of cooldown method: list of result_dataclass objects with the results
    of the two-state discrimination output for each qubit}
    """

    #####################################
    #  Open Communication with the QOP  #
    #####################################
    # qmm = QuantumMachinesManager(qop_ip)

    # connecting with Theo's credentials
    qmm = QuantumMachinesManager(
        host="theo-4c195fa0.dev.quantum-machines.co",
        port=443,
        credentials=create_credentials())

    results_dict = {}

    for reset_function_name, reset_function_settings in reset_dictionary.items():

        reset_program = generate_reset_program(reset_function_name, reset_function_settings)
        results_dataclass = run_and_format(reset_program, qmm, simulation=True)

        results_dict[reset_function_name] = results_dataclass

    launch_reset_gui(results_dict)
    return results_dict


if __name__ == '__main__':
    reset_dictionary = {
        'Cooldown': {'macro': 'cooldown', 'settings': {'cooldown_time': 8}},
        'Active threshold 1': {'macro': 'active', 'settings': {'threshold': -0.003, 'max_tries': 3}},
        'Active threshold 2': {'macro': 'active', 'settings': {'threshold': -0.005, 'max_tries': 5}}
    }

    results_dictionary = compare_reset(reset_dictionary)










