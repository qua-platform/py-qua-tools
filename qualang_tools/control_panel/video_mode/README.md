# Video Mode

This module performs a continuous rapid 2D scan of two sweep axes, and measures a signal at each point. The results are shown through an interactive web frontend with a live plot and controls for the sweep parameters.

The video mode has been designed as a modular tool that is composed of four parts:

1. The `OPXDataAcquirer` class, which is responsible for the data acquisition.
2. The `ScanMode` class, which is responsible for how the 2D grid is traversed.
3. The `InnerLoopAction` class, which is responsible for what QUA code is performed during each step of the scan.
4. The `VideoMode` class, which handles interaction with the frontend.

The `ScanMode` and `InnerLoopAction` classes are highly flexible and can be selected/modified to suit the specific needs of the user. For example, three different scan modes (`RasterScan`, `SpiralScan`, and `SwitchRasterScan`) are provided, which can be used to acquire data in different ways. Similarly, the `InnerLoopAction` class can be modified to perform additional actions, such as adding specific pulses prior to each measurement.

## Installation

First, it is necessary to install the `qualang_tools` package with the `videomode` extra packages:

```bash
pip install qualang-tools[videomode]
```

## Basic Usage
To use the video mode, it is necessary to initialize the relevant classes and pass them to the `VideoMode` class. 
We will go through a simple example to demonstrate the video mode. Most of the classes and functions described here have additional options which can be found in the docstrings and in the source code.

If you don't have access to an OPX but still want to try the video mode, see the `Simulated Video Mode`section in `Advanced Usage`

First, we assume that the machine is already connected.
```python
qmm, qm = connect_qua_machine()
```

Next we define the scan mode, which in this case is a raster scan.
```python
from qualang_tools.control_panel.video_mode import scan_modes
scan_mode = scan_modes.RasterScan()
```

Next we define the inner loop action, which in this case is a QUA program that performs a measure of the readout pulse.
```python
# Define the inner loop action
# In this case 
from qualang_tools.control_panel.video_mode.inner_loop_actions import InnerLoopAction
inner_loop_action = InnerLoopAction(
    x_element="output_ch1",  # Must be a valid QUA element
    y_element="output_ch2",  # Must be a valid QUA element
    readout_element="measure_ch",  # Must be a valid QUA element
    readout_pulse=readout_pulse,  # Name of the readout pulse registered in the readout_element
)
```

Next we define the sweep axes, which define the values that the 2D scan will take as coordinates.

```python
from qualang_tools.control_panel.video_mode.sweep_axis import SweepAxis
x_axis = SweepAxis(
    name="voltage_gate1",  # Sweep axis name, used among others for plotting
    span=0.03,  # Span of the sweep in volts
    points=51,  # Number of points to sweep
)
y_axis = SweepAxis(name="voltage_gate2", span=0.03, points=51)
```
The `SweepAxis` contains additional attributes, such as attenuation and a voltage offset, the latter of which is described in `Advanced Usage`.

Next we define the data acquirer, which is the object that will handle the data acquisition.
```python
from qualang_tools.control_panel.video_mode.data_acquirer import OPXDataAcquirer
data_acquirer = OPXDataAcquirer(
    qm=qm,
    qua_inner_loop_action=inner_loop_action,
    scan_mode=scan_mode,
    x_axis=x_axis,
    y_axis=y_axis,
)
```

You can now test the data acquirer before using it in video mode.
```python
data_acquirer.run_program()
results = data_acquirer.acquire_data()
```

Finally, we can start the video mode.
```python
from qualang_tools.control_panel.video_mode.video_mode import VideoMode
video_mode = VideoMode(data_acquirer=data_acquirer)
video_mode.run()
```

Note that if you want to run this code in an interactive environment such as a Jupyter notebook, you should use `video_mode.run(use_reloader=False)`.

You can now access video mode from your browser at `http://localhost:8050/` (the port may be different, see the output logs for details).


## Advanced Usage
### Voltage offsets

The `SweepAxis` class has an `offset_parameter` attribute, which is an optional parameter that defines the sweep offset. This can be a QCoDeS DC voltage source parameter or a `VoltageParameter` object.

As an example, let us assume that we have a QCoDeS parameter `x_gate` for the DC voltage of a gate:

```python
x_offset()  # Returns the DC voltage, e.g. 0.62
```

In this case, we can pass this parameter to the `SweepAxis` class to define the sweep offset.
```python
x_axis = SweepAxis(name="gate", span=0.03, points=51, offset_parameter=x_offset)
```
The video mode plot should now correctly show the sweep axes with the correct offset.

Note that if the offset voltage is changed, it will need to be changed in the same kernel where the video mode is running. One solution for this is using the `VoltageControl` module in py-qua-tools.


### Simulated Video Mode
Below is an example of how to run the video mode without an actual OPX.
In this case, we will use the `RandomDataAcquirer` class, which simply displays uniformly-sampled random data.
```python
from qualang_tools.control_panel.video_mode import *

x_axis = SweepAxis(name="X", span=0.1, points=101)
y_axis = SweepAxis(name="Y", span=0.1, points=101)

data_acquirer = RandomDataAcquirer(
    x_axis=x_axis,
    y_axis=y_axis,
    num_averages=5,
)

live_plotter = VideoMode(data_acquirer=data_acquirer)
live_plotter.run()
```

