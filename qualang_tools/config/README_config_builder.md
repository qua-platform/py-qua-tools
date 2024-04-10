# Deprecation Warning

ConfigBuilder is no longer being actively developed and may not support all config functionality.
To use, you need to install the package using `pip instal qualang_tools[configbuilder]`

# Config module

## Introduction
---------------
The goal of the config module is to simplify the generation of QUA configuration necessary for your QUA program. In this module we provide user-friendly classes and a `ConfigBuilder` class to procedurally build a QUA configuration.

## Components
--------------

We provide classes (essentially wrappers to the underlying dictionary) for all fields that appear in the configuration and methods that help you to manipulate them.

 <ins> **Controller** </ins>

 A Quantum Orchestration Platform controller class. It can be initialized simply by providing the controller name and type (the default is `opx1`).

 ```python
 cont = Controller("con1")
 ```
 
 All digital & analog ports that you use in any quantum element can be opened through the methods: `analog_output`, `analog_input`, `digital_input`, `digital_output`.

 For example, to open (if it is not already open) and get an instance of analog output with port id 5 and offset 0.2, you can do,

```python
port = cont.analog_output(5, 0.2)
```

The additional attributes of ports can be directly accessed or set from the instance of the port. For the AnalogOutputPort that we just opened we can configure the additional attributes as shown below:
```python
 port.delay = 32
 port.filter = AnalogOutputFilter([1.0, 1.5], [1.4, 2.5])
```

<ins> **Waveforms** </ins>

There are three types of waveforms `ConstantWaveform`, `ArbitraryWaveform` and `DigitalWaveform`. These objects can be created by specifying the names and the sample(s) as follows:

```python
cont_wf = ConstantWaveform("wf1", 0.2)
arb_wf = ArbitraryWaveform("wf2", [0.2, 0.1, 0.0])
digital_wf = DigitalWaveform("wf3", [(1, 16)])
```

Each waveform object once created can be shared among several different pulses.
 
<ins> **Pulses** </ins>

There are two types of pulses `ControlPulse` and `MeasurePulse`. These can be initialized by specifying the name, list of waveforms and their durations.

```python
pulse1 = ControlPulse("p1", [ConstantWaveform("wf1",0.5), ConstantWaveform("wf1",0.5)], 16)
pulse2 = MeasurePulse("p2", [ConstantWaveform("wf1",0.5), ConstantWaveform("wf1",0.5)], 16)
```

In addition for `MeasurePulse`s we can add digital markers and weights (see below) with the `add` method.

```python
pulse2.add(digital_wf)
```

<ins> **IntegrationWeights**  </ins>

There are two types of integration weights `ConstantIntegrationWeights` and `ArbitraryIntegrationWeights`. `ConstantIntegrationWeights` are initialized by specifying the name, the cosine and sine values and the duration.

```python
const_iw = ConstantIntegrationWeights("iw1", 1.0, 0.0, 16)
```
Similarly, `ArbitraryIntegrationWeights` are initialized as follows by providing the list of cosine and sine values.
```python
arb_iw = ConstantIntegrationWeights("iw2", [1.0, 0.2], [0.0, -0.2], 2)
```

In order to add integration weights to a `MeasurePulse` you need to give a name that can be then used in a QUA measure statement. We introduced `Weights` (nothing but a named `IntegrationWeights`) to facilitate this. Consider the following two ways of adding `Weights`:

```python
pulse2.add(Weight(const_iw))
```
or 
```python
pulse2.add(Weight(const_iw, "my_iw"))
```
in the first case, you will use `iw1` in the `measure` statement, whereas in the second case, you will use `my_iw` to refer to the integration weights.

<ins> **Mixers** </ins>

A microwave mixer is initialized with the name, lo_frequency, intermediate_frequency and a correction matrix,
```python
mixer = Mixers("mx1", 5e9, 4e6, Matrix2x2([[1, 0],[0, 1]]))
```
Mixers can be added to an `Element` or `MeasureElement` (see below) with the `add` method.

<ins> **Elements and collection of elements...** </ins>

An element describes a control entity which is connected to some ports of the controller. It can be initialized by specifying the name, list of Analog/Digital Input/Output ports and optionally `intermediate_frequency` or `lo_frequency` (if inputs are mixed by the element).

A `MeasureElement` has additional methods to set time of flight and smearing parameters needed while acquiring measurement data.

In general, to interface with any experimental device you would need a collection of `Element`s. The class `ElementCollection` is useful in such cases. We provide few example objects (`Transmon`, `ReadoutResonator`, `FluxTunableTransmon` etc.) common to superconducting qubit experiments, you are encouraged to inherit from `ElementCollection` and expand wherever necessary.

**Note**: The existing component classes and their attributes are based on the OpenAPI specification of QM Config ```v0.3.5-rc1```. If there are any updates to the QM config schema, the component classes should be modified accordingly.

## ConfigBuilder
----------------

Add all components to the `ConfigBuilder`. The configuration is generated at the very end upon calling the `build` method. Therefore, the precise order in which you add the objects to `ConfigBuilder` is not important. Modifications to the objects already added to the `ConfigBuilder` are reflected in the final configuration. However, note that consistency checks between different components are not done within the builder. The validity of the configuration is verified by the compiler when you eventually run the QUA program.
For more details, check the examples in `qua-libs/examples/config-builder/`.

## Parameters
--------------

There are several usecases where it is useful to write a QUA configuration without assigning a specific value to component attributes for e.g. fields based on some calibration data that can change everyday. `ConfigVar` class maintains a dictionary of parameters, it helps you to write a generic configuration with parametric values. For example, in the following code

```python
p = ConfigVar()
wf = ConstantWaveform("wf1", p.parameter("sample"))
```

the value of the constant waveform is initialised with a parameter called `sample`, the waveform object can be further used in other components added to config builder. Here the `parameter` method returns a lambda function, you may access the value of the parameter (if it is already set, otherwise you get an `AssertionError`) by calling this lambda function.

```python
p.set(sample=2.0)
print(p.parameter("sample"))
```
Finally, to generate an instance of the configuration it is enough to set all parameters used in the config builder before calling the `build` method.