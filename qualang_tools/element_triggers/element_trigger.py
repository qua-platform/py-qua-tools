"""calling function libraries"""
import configparser
import copy

from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
from configuration import *
import matplotlib.pyplot as plt
import numpy as np


def decide(input1, IO2, elements):
    with if_(input1 >= len(elements)):
        assign(input1, input1 - len(elements))
        with switch_(input1):
            for i in range(len(elements)):
                with case_(i):
                    amplitude(elements[i], IO2)
    with else_():
        with switch_(input1):
            for i in range(len(elements)):
                with case_(i):
                    frequency(elements[i], IO2)


def frequency(element, IO2):
    freq = declare(int)
    assign(freq, IO2)
    update_frequency(element, freq)


def amplitude(element, IO2):
    a = declare(fixed)
    assign(a, IO2)
    play("play"*amp(a),element)


def amp_or_freq(input1, input2, check, elements):
    if check == 1:
        QM1.set_io2_value(float(input2))
        QM1.set_io1_value(int(input1)+len(elements))
    if check == 2:
        QM1.set_io2_value(int(float(input2)))
        QM1.set_io1_value(int(input1))


def config_update(config_original):
    config = copy.deepcopy(config_original)
    config1 = {}
    config2 = {}
    config1['version'] = 1
    for controller in list(config["controllers"].keys()):
        config1['controllers'] = {}
        config1['controllers'][controller] = {"type": "opx1", "analog_outputs": {}}
        config1['controllers'][controller]["analog_outputs"] = config['controllers'][controller]["analog_outputs"]
    config1['elements'] = {}
    config1['waveforms'] = {'zero_wf': {"type": "constant", "sample": 0.0}, 'const_wf':{"type": "constant", "sample": 0.5} }
    config1['pulses'] = {}
    config1['pulses']['single_on'] = {
        "operation": "control",
        "length": 16,
        "waveforms": {"single": "const_wf"},
    }
    config1['pulses']['IQ_Ion'] = {
        "operation": "control",
        "length": 16,
        "waveforms": {
            "I": "const_wf",
            "Q": "zero_wf",
        },
    }
    elements = list(config["elements"].keys())
    config2['version'] = 1
    for controller in list(config["controllers"].keys()):
        config2['controllers'] = {controller: {"type": "opx1", "digital_outputs": {}}}
        config2['controllers'][controller]["digital_outputs"] = config['controllers'][controller]["digital_outputs"]
    config2['elements'] = {}
    config2['pulses'] = {'digital_ON': {
        "digital_marker": "ON",
        "length": 1000,
        "operation": "control",
    }}
    config2['digital_waveforms'] = {'ON': {"samples": [(1, 0)]}}
    for element in elements:
        if bool(config['elements'][element].get("digitalInputs")):
            config2['elements'][element] = {"operations": {
                "ON": "digital_ON",
            }}
            config2['elements'][element]["digitalInputs"] = config['elements'][element]["digitalInputs"]

    for i in range(len(elements)):
        if bool(config['elements'][elements[i]].get("mixInputs")):
            config1['elements'][elements[i]] = config['elements'][elements[i]]
            if bool(config1['elements'][elements[i]].get("digitalInputs")):
                config1['elements'][elements[i]].pop("digitalInputs")
            if bool(config1['elements'][elements[i]].get("outputs")):
                config1['elements'][elements[i]].pop("outputs")
                config1['elements'][elements[i]].pop("time_of_flight")
                config1['elements'][elements[i]].pop("smearing")
            config1['elements'][elements[i]].pop("operations")
            config1['elements'][elements[i]]['operations'] = {'play': 'IQ_Ion'}

        elif bool(config['elements'][elements[i]].get("singleInput")):
            config1['elements'][elements[i]] = config['elements'][elements[i]]
            if bool(config1['elements'][elements[i]].get("digitalInputs")):
                config1['elements'][elements[i]].pop("digitalInputs")
            config1['elements'][elements[i]].pop("operations")
            config1['elements'][elements[i]]['operations'] = {'play': 'single_on'}

    return config1, config2


def element_analog(elements, config):

    # QMm = QuantumMachinesManager()
    QMm = QuantumMachinesManager(host='172.16.2.122', port='80')
    QM1 = QMm.open_qm(config, True)

    """The QUA program"""
    with program() as prog:
        io_var1 = declare(int)
        for i in range(len(elements)):
            play('play'*amp(0), elements[i])
        with infinite_loop_():
            pause()
            assign(io_var1, IO1)
            decide(io_var1, IO2, elements)

    return QM1.execute(prog), QM1

    # return QM1.simulate(prog,
    #                    SimulationConfig(int(5000)))  # running a simulation for a specific time in clock cycles, 4 ns


def element_digital(element_ON, digital_elements, config):
    # QMm = QuantumMachinesManager()
    QMm = QuantumMachinesManager(host='172.16.2.122', port='80')
    QM1 = QMm.open_qm(config, False)
    with program() as prog:
        for i in range(len(element_ON)):
            if element_ON[i]:
                with infinite_loop_():
                    play("ON", digital_elements[i])
    return QM1.execute(prog), QM1
    # return QM1.simulate(prog,
    #                    SimulationConfig(int(5000))), QM1  # running a simulation for a specific time in clock cycles, 4 ns


def update_analog(element, value):
    if isinstance(value, int):
        change_freq = 2
        analog_data[element]['frequency'] = value
    else:
        change_freq = 1
        value_tmp = value
        value = (value - analog_data[element]['amplitude']) * 2
        analog_data[element]['amplitude'] = value_tmp
    while job.is_paused():
        amp_or_freq(analog_elements.index(element), value, change_freq, analog_elements)
        job.resume()
        break


def update_amplitude(element, value):
    value_tmp = value
    value = (value - analog_data[element]['amplitude']) * 2
    analog_data[element]['amplitude'] = value_tmp
    while job.is_paused():
        amp_or_freq(analog_elements.index(element), value, 1, analog_elements)
        job.resume()
        break


def update_frequency(element, value):
    analog_data[element]['frequency'] = value
    while job.is_paused():
        amp_or_freq(analog_elements.index(element), value, 2, analog_elements)
        job.resume()
        break


def show_digital():
    for i in range(len(digital_elements)):
        print(f'{i}: ' + digital_elements[i] + ' - ' + str(dig_elements_ON[i]))


def choose_digital(*digital_change):
    for element in digital_elements:
        if element in digital_change:
            dig_elements_ON[digital_elements.index(element)] = bool(int(dig_elements_ON[digital_elements.index(element)])-1)
    show_digital()


[config_analog, config_digital] = config_update(config)
analog_elements = list(config_analog["elements"].keys())
digital_elements = list(config_digital["elements"].keys())
analog_data = {}
for element in analog_elements:
    analog_data[element] = {'amplitude' : 0, 'frequency': config_analog['elements'][element]['intermediate_frequency']}
dig_elements_ON = [False]*len(digital_elements)

# , dig_elem = digital_elements, dig_elements_ON = dig_elements_ON

[job, QM1] = element_analog(analog_elements, config_analog)
# dig_elements_ON = choose_digital(digital_elements)
# [job_dig, QM2] = element_digital(dig_elements_ON, digital_elements, config_digital)
# while job.is_paused():
#     if update_analog(analog_elements):
#         break
#     job.resume()
# job.halt()
# job_dig.halt()
# QM1.close()
# QM2.close()


"""getting the simulated samples of the OPX output and plotting them"""
# samples = job_dig.get_simulated_samples()
# samples.con1.plot()


