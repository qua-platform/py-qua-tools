# Manual output control

## Introduction

This module allows controlling the outputs from the OPX in CW mode. Once created, it has an API for defining which channels are on. Analog channels also have an API for defining their amplitude and frequency.

You can either:
- Use an existing configuration dictionary, or
- Specify the ports directly via `ManualOutputControl.ports(...)`
---
## Usage Example
### Starting and controlling the output using a configuration file

This opens up a control panel using an existing configuration. The outputs are controlled by specifying the elements which are connected to them.
```python
from qualang_tools.control_panel import ManualOutputControl
manual_output_control = ManualOutputControl(config)
manual_output_control.turn_on_element('qubit')
manual_output_control.set_amplitude('qubit', 0.25)
manual_output_control.digital_off('qubit')
manual_output_control.digital_on('laser')
```
Note: If the config's controllers contain "fems", OPX1000 mode is automatically detected.

### Starting and controlling the output by specifying the output ports
This opens up a control panel by directly specifying which ports to control.
The outputs are controlled by specifying their port numbers in the API.
For OPX+ or OPX1, ports are defined by integers 1-10 per controller. For example, controller 3, port 2 -> 32.
```python
from qualang_tools.control_panel import ManualOutputControl
# This opens up a control panel for controlling digital ports 1,2,3,4. Analog port 1,2,5 are controlled as single analog outputs and (3,4) as an IQ pair.
manual_output_control = ManualOutputControl.ports(analog_ports=[1, 2, (3,4), 5], digital_ports=[1, 2, 3, 4])
manual_output_control.set_frequency((3,4), 50e6)
manual_output_control.set_amplitude((3,4), 0.25)
manual_output_control.set_frequency(5, 25e6)
manual_output_control.set_amplitude(6, 0.25)
manual_output_control.digital_on(2)
```
In OPX1000, ports are defined by (controller, fem, port) tuples, where: controller is a string, e.g. "con1", fem is the FEM index (integer), port is the physical output on that FEM (integer).
You must specify (or accept defaults for): fem_types: which FEMs are "LF" vs "MW", mw_output_params: optional per-port settings for MW FEM outputs.
```python
from qualang_tools.control_panel import ManualOutputControl

# Define FEM types: ("controller", fem_id) -> "LF" or "MW"
fem_types = {
    ("con1", 1): "LF",
    ("con1", 2): "MW",
}

# Optional MW FEM output parameters: (controller, fem, port) -> dict of settings
mw_output_params = {
    ("con1", 2, 1): {
        "band": 2,
        "full_scale_power_dbm": -11,
        "sampling_rate": 1e9,
        "upconverter_frequency": 5e9,
    },
}

manual_output_control = ManualOutputControl.ports(
    isopx1k=True,  # OPX1000 mode
    analog_ports=[
        ("con1", 1, 1),                                # LF FEM: single output
        (("con1", 1, 2), ("con1", 1, 3)),              # LF FEM: IQ pair
        ("con1", 2, 1),                                # MW FEM: single output
    ],
    digital_ports=[
        ("con1", 1, 4),                                # digital output on LF FEM
        ("con1", 2, 2),                                # digital output on MW FEM
    ],
    fem_types=fem_types,
    mw_output_params=mw_output_params,
)
# You can pass the same tuples to refer to elements
manual_output_control.set_frequency(("con1", 1, 1), 50e6)
manual_output_control.set_amplitude(("con1", 1, 1), 0.25)
iq_element = (("con1", 1, 2), ("con1", 1, 3))
manual_output_control.set_frequency(iq_element, 75e6)
manual_output_control.set_amplitude(iq_element, 0.25)
manual_output_control.digital_on(("con1", 1, 4))
manual_output_control.digital_off(("con1", 2, 2))
```
## List of functions

* manual_output_control = ManualOutputControl(configuration, host=None, port=None, cluster_name=None, close_previous=True, elements_to_control=None, isopx1=False) - 
        Gets a QUA configuration file and creates two different QuantumMachines. One QM continuously runs all the
        analog ports and one continuously runs all the digital ports. This enables controlling the amplitude and
        frequency of the analog ports and turning on and off the digital ports.
        All digital outputs start turned off, and all analog outputs start with zero amplitude, but with the frequency
        from the configuration. 
    * configuration - a python dictionary containing the QUA configuration
    * host - The host or IP of the QOP. Defaults to `None`: local settings are used.
    * port - The port used to access the QOP. Defaults to `None`, local settings are used.
    * cluster_name - The name of the cluster. Defaults to `None`. Requires redirection between devices.
    * close_previous -  Close currently running Quantum Machines. Note that if False, and a Quantum Machine which uses the same ports is already open, then this function would fail.
    * elements_to_control - A list of elements to be controlled. If empty, all elements in the config are included. Useful if the configuration contain more elements then can be used in parallel.
    * isopx1 - Set to `True` if using OPX1. Defaults to `False`.
* manual_output_control = ManualOutputControl.ports(isopx1k=False, analog_ports=None, digital_ports=None, host=None, port=None, cluster_name=None, close_previous=True, fem_types=None, mw_output_params=None) -
        Gets a list of analog and digital channels and creates two different QuantumMachines. One QM continuously runs
        all the analog ports and one continuously runs all the digital ports. This enables controlling the amplitude and
        frequency of the analog ports and turning on and off the digital ports.
        All digital outputs start turned off, and all analog outputs start with zero amplitude and zero frequency.
    * isopx1k: False->OPX+/OPX1 mode, True->OPX1000 mode
    * analog_ports: The list of analog ports to control. A tuple creates an IQ pair.
     For OPX+ or OPX1, [1, 2, (3, 4)] creates two independent channels at ports 1 & 2, and one IQ pair at ports 3 & 4.
     For multiple controllers, increase the port by 10. For example, controller 3 port 2 should be 32.
     For OPX1000, [("con1", 1, 1), ("con1", 1, 2), (("con1", 1, 3),("con1", 1, 4))] creates two independent channels at ports 1&2 for FEM 1 in controller "con1", and one IQ pair at ports 3&4 for FEM 1 in controller "con1". 
    * digital_ports: The list of digital ports to control.
     For multiple OPX+ or OPX1 controllers, increase the port by 10. For example, controller 3 port 2 should be 32.
     For OPX1000, digital ports are defined by a list of tuples, e.g. [("con1", 1, 1),("con1", 1, 2)].
    * host: The host or IP of the QOP. Defaults to `None`: local settings are used.
    * port: The port used to access the QOP. Defaults to `None`, local settings are used.
    * cluster_name = The name of the cluster. Defaults to `None`. Requires redirection between devices.
    * close_previous: Close currently running Quantum Machines. Note that if False, and a Quantum Machine
                             which uses the same ports is already open, then this function would fail.
    * fem_types: Required when using OPX1000 if you have MW FEMs; otherwise FEMs default to type "LF". Python dict mapping (controller, fem_id) -> "LF" or "MW". e.g. fem_types={("con1", 1): "LF" ,("con1", 2): "MW",("con1", 3): "MW",}.
    If an existing FEM is created with one type and fem_types requests a different type, an exception is raised.
    * mw_output_params: Optional dict mapping (controller, fem, port)->dict of MW output settings. If not provided for a given MW output, defaults are used: sampling_rate=1e9, band=2, full_scale_power_dbm=-11,upconverter_frequency=5e9. e.g. mw_output_params={("con1", 2, 1): {"band": 2,
    "full_scale_power_dbm": -11, "sampling_rate": 1e9, "upconverter_frequency": 5e9,}}
* turn_on_element(element, amplitude, frequency) - Turns on the digital and analog outputs of a given element
    * element: An element to be turned on.
    * amplitude: The amplitude of the analog output of the element. If no amplitude is given, uses maximum amplitude.
    * frequency: The frequency of the analog output of the element.  If no frequency is given, uses last frequency used.
* turn_off_elements(*elements) - Turns off the digital and analog for all the given elements. If no elements are given, turns off all elements.
    * elements: A variable number of elements to be turned off
* set_amplitude(element, value) - Set the amplitude of an analog element.
    * element: the name of the analog element to be updated. If element is no in the configuration, the function will exit.
    * value: the new amplitude of the analog element. If input abs(value) is greater than (0.5 - 2^16), the function will exit.
* set_frequency(element, value) - Set the frequency of an analog element.
    * element: the name of the analog element to be updated. If element is no in the configuration, the function will exit.
    * value: the new frequency of the analog element. If element frequency is set to None, the function will exit.
* digital_on(*digital_element) - Turns on all digital elements inputted by the user. If no input is given, turns on all elements.
    * digital_element: A variable number of elements to be turned on
* digital_off(*digital_element) - Turns off all digital elements inputted by the user. If no input is given, turns off all elements.
    * digital_element: A variable number of elements to be turned off
* digital_switch(*digital_element) - Switches the state of the given digital elements from on to off, and from off to on.
    * digital_element: A variable number of elements to be turned switched
* analog_status() - Returns a dictionary of the analog elements, with their current amplitude and frequency.
* digital_status() - Returns a dictionary of the digital elements, with their current status.
* print_analog_status() - Prints a list of the analog elements, with their current amplitude and frequency.
* print_digital_status()  - Prints a list of the digital elements, with a True (False) to indicate the element is on (off).
* close - Halts all jobs sent to the OPX and then closes the quantum machine.
