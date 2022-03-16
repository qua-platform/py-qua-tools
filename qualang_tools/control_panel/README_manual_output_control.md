# Manual output control

## Introduction

This module allows controlling the outputs from the OPX in CW mode. Once created, it has an API for defining which channels are on. Analog channels also have an API for defining their amplitude and frequency.

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

### Starting and controlling the output by specifying the output ports
This opens up a control panel by directly specifying which ports to control.
The outputs are controlled by specifying their port numbers in the API.
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

## List of functions

* manual_output_control = ManualOutputControl(configuration, host=None, port=None, close_previous=True, elements_to_control=None) - 
        Gets a QUA configuration file and creates two different QuantumMachines. One QM continuously runs all the
        analog ports and one continuously runs all the digital ports. This enables controlling the amplitude and
        frequency of the analog ports and turning on and off the digital ports.
        All digital outputs start turned off, and all analog outputs start with zero amplitude, but with the frequency
        from the configuration. 
    * configuration - a python dictionary containing the QUA configuration
    * host - The host or IP of the QOP. Defaults to `None`: local settings are used.
    * port - The port used to access the QOP. Defaults to `None`, local settings are used.
    * close_previous -  Close currently running Quantum Machines. Note that if False, and a Quantum Machine which uses the same ports is already open, then this function would fail.
    * elements_to_control - A list of elements to be controlled. If empty, all elements in the config are included. Useful if the configuration contain more elements then can be used in parallel.
* manual_output_control = ManualOutputControl.ports(analog_ports=None, digital_ports=None, host=None, port=None, close_previous=True) -
        Gets a list of analog and digital channels and creates two different QuantumMachines. One QM continuously runs
        all the analog ports and one continuously runs all the digital ports. This enables controlling the amplitude and
        frequency of the analog ports and turning on and off the digital ports.
        All digital outputs start turned off, and all analog outputs start with zero amplitude and zero frequency.
    * analog_ports: The list of analog ports to control. A tuple creates an IQ pair.
     For example, [1, 2, (3, 4)] creates two independent channels at ports 1 & 2, and one IQ pair at ports 3 & 4.
     For multiple controllers, increase the port by 10. For example, controller 3 port 2 should be 32.
    * digital_ports: The list of digital ports to control.
     For multiple controllers, increase the port by 10. For example, controller 3 port 2 should be 32.
    * host: The host or IP of the QOP. Defaults to `None`: local settings are used.
    * port: The port used to access the QOP. Defaults to `None`, local settings are used.
    * close_previous: Close currently running Quantum Machines. Note that if False, and a Quantum Machine
                             which uses the same ports is already open, then this function would fail.)
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
