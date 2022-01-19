# Manual control Panel

## Introduction
---------------
This module introduces a class that recives a configuration file, separate it into two configuration files, one containing the analog elements, and one containing the digital elements. Then creates two quantum machines instances
that can run in parallel and provide a set of API function that enables the user to manualy turn on/off each digital element, and set the amplitude and frequency of each analog element.

## Parameters
---------------
configuration - a python dictionary containing the QUA configuration
host - The host or IP of the QOP. Defaults to `None`: local settings are used.
port - The port used to access the QOP. Defaults to `None`, local settings are used.
close_previous -  Close currently running Quantum Machines. Note that if False, and a Quantum Machine which uses the same ports is already open, then this function would fail.
elements_to_control - A list of elements to be controlled. If empty, all elements in the config are included. Useful if the configuration contain more elements then can be used in parallel.

## List of functions
---------------

set_amplitude(element, value) - Set the amplitude of an analog element.
	element: the name of the analog element to be updated. If element is no in the configuration, the function will exit.
	value: the new amplitude of the analog element. If input abs(value) is greater than (0.5 - 2^16), the function will exit.
	
set_frequency(element, value) - Set the frequency of an analog element.
	element: the name of the analog element to be updated. If element is no in the configuration, the function will exit.
	value: the new frequency of the analog element. If element frequency is set to None, the function will exit.
	
digital_status() - Prints the list of digital elements with their current state (on/off).

analog_status() - Prints the list of analog elements with their current amplitude and frequency.

digital_switch(digital_element) - Switches the state of the given digital elements from on to off, and from off to on.
	digital_element: A variable number of elements to be turned switched

digital_on(digital_element) - Turns on all digital elements inputted by the user. If no input is given, turns on all elements.
	digital_element: A variable number of elements to be turned on

digital_off(digital_element) - Turns off all digital elements inputted by the user. If no input is given, turns off all elements.
	digital_element: A variable number of elements to be turned off

turn_off_elements(elements) - Turns off the digital and analog for all the given elements. If no elements are given, turns off all elements.
	elements: A variable number of elements to be turned off

turn_on_element(element, amplitude, frequency) - Turns on the digital and anlog ouputs of a given element
	element: An element to be turned on.
	amplitude: Amplitude of the analog output of the element. If no amplitude is given, uses maximum amplitude.
	frequency: Frequency of the analog output of the element.  If no frequency is given, uses last frequency used.