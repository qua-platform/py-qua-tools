# Config module

## Introduction
---------------
The goal of the config module is to simplify the generation of QUA configuration necessary for your QUA program. In this module we provide user-friendly classes and a `ConfigBuilder` class to procedurally build a QUA configuration.

## Components
--------------

We provide a class (essentially wrappers to the underlying dictionary) for all fields that appear in the configuration and methods that help you to manipulate them.

 <ins> **Controller** </ins>

 A Quantum Orchestration Platform controller class. It can be initialized simply by providing the controller name and type (the default is `opx1`).

 ```
 cont = Controller("con1")
 ```
 
 All digital & analog ports that you use in any quantum element can be opened through the methods: `analog_output`, `analog_input`, `digital_input`, `digital_output`.

 For example, to open (if it is not already open) and get an instance of analog output with port id 5 and offset 0.2, you can do,

```
port = cont.analog_output(5, 0.2)
```

The additional attributes of ports can be directly accessed or set from the instance of the port. For the AnalogOutputPort that we just opened we can configure the additional attributes as shown below:
```
 port.delay = 32
 port.filter = AnalogOutputFilter([1.0, 1.5], [1.4, 2.5])
```

<ins> **Waveforms** </ins>

There are three types of waveforms `ConstantWaveform`, `ArbitraryWaveform` and `DigitalWaveform`. These objects can be created by specifying the names and the sample(s) as follows:

```
cont_wf = ConstantWaveform("wf1", 0.2)
arb_wf = ArbitraryWaveform("wf2", [0.2, 0.1, 0.0])
digital_wf = DigitalWaveform("wf3", [(1, 16)])
```

Each waveform object once created can be shared among several different pulses.
 
<ins> **Pulses** </ins>

There are two types of pulses `ControlPulse` and `MeasurePulse`. These can be initialized by specifying the name, list of waveforms and their durations.

```
pulse1 = ControlPulse("p1", [ConstantWaveform("wf1",0.5), ConstantWaveform("wf1",0.5)], 16)
pulse2 = MeasurePulse("p2", [ConstantWaveform("wf1",0.5), ConstantWaveform("wf1",0.5)], 16)
```

In addition for `MeasurePulse`s we can add digital markers and weights (see below) with the `add` method.

```
pulse2.add(digital_wf)
```

<ins> **IntegrationWeights**  </ins>

There are two types of integration weights `ConstantIntegrationWeights` and `ArbitraryIntegrationWeights`. `ConstantIntegrationWeights` are initialized by specifying the name, the cosine and sine values and the duration.

```
const_iw = ConstantIntegrationWeights("iw1", 1.0, 0.0, 16)
```
Similarly, `ArbitraryIntegrationWeights` are initialized as follows by providing the list of cosine and sine values.
```
arb_iw = ConstantIntegrationWeights("iw2", [1.0, 0.2], [0.0, -0.2], 2)
```

In order to add integration weights to a `MeasurePulse` you need to give a name that can be then used in a QUA measure statement. We introduced `Weights` (nothing but a named `IntegrationWeights`) to facilitate this. Consider the following two ways of adding `Weights`:

```
pulse2.add(Weight(const_iw))
```
or 
```
pulse2.add(Weight(const_iw, "my_iw"))
```
in the first case, you will use `iw1` in the `measure` statement, whereas in the second case, you will use `my_iw` to refer to the integration weights.

<ins> **Mixers** </ins>



<ins> **Elements and collection of elements** </ins>
 

**Note**: The existing component classes and their attributes are based on the OpenAPI specification of QM Config ```v0.3.5-rc1```. If there are any updates to the QM config schema, the component classes should be modified accordingly.

## ConfigBuilder
----------------

Add all components to the ```ConfigBuilder```. The configuration is generated at the very end upon calling the ```build``` method, therefore the precise order in which you add the objects to the ```ConfigBuilder``` is not important. Modifications to the objects already added to the ```ConfigBuilder``` are reflected in the final configuration. However, note that the consistency checks between different components you add are not done within the builder. The validity of the configuration is verified by the compiler when you eventually run the QUA program.


## Parameters
--------------