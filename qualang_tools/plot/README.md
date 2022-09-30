# Plot tools
This library includes tools to help handling plots from QUA programs.

## interrupt_on_close
This function allows to interrupt the execution and free the console when closing the live-plotting figure.

### Usage example

```python
from qm.QuantumMachinesManager import QuantumMachinesManager
from qualang_tools.plot import interrupt_on_close
from qm.qua import *
import matplotlib.pyplot as plt
from configuration import config

with program() as test_prog:
    # The QUA program to execute
    ...

qmm = QuantumMachinesManager()
qm = qmm.open_qm(config)
job = qm.execute(test_prog)

fig = plt.figure()
interrupt_on_close(fig, job)

while job.result_handles.is_processing():
    # Live plotting
    ...
    # The execution will be cleanly interrupted by closing the figure
```

## plot_demodulated_data 1D and 2D
These functions plot the demodulated data (either 'I' and 'Q' or amplitude and phase) from a 1D or 2D scan.

### Usage example

```python
from qualang_tools.plot import plot_demodulated_data_1d, plot_demodulated_data_2d
import numpy as np

time = np.linspace(0,1000, 1001)
amp = np.linspace(-2, 2, 101)
I = np.array([[np.sin(i/100)*np.cos(k) for i in time] for k in amp])
Q = np.array([[np.cos(i/100)*np.sin(k) for i in time] for k in amp])

plot_demodulated_data_2d(time, amp, I, Q, "time [ns]", "amplitude [mV]", "2D map", amp_and_phase=True, plot_options={"cmap": "magma"})
```

## get_simulated_samples_by_element
This function gets the samples generated from the QUA simulator element per element.

### Usage example

```python
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import SimulationConfig
from qm.qua import *
from configuration import config
from qualang_tools.plot import get_simulated_samples_by_element

with program() as test_prog:
    # The QUA program to simulate
    ...

qmm = QuantumMachinesManager()
simulation_config = SimulationConfig(duration=8000)
job = qmm.simulate(config, test_prog, simulation_config)
qubit_samples = get_simulated_samples_by_element("qubit", job, config)
resonator_samples = get_simulated_samples_by_element("resonator", job, config)
```


## plot_simulator_output
This function plots the samples generated from the QUA simulator element per element using *plotly*.

### Usage example

```python
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import SimulationConfig
from qm.qua import *
from configuration import config
from qualang_tools.plot import plot_simulator_output

with program() as test_prog:
    # The QUA program to simulate
    ...

qmm = QuantumMachinesManager()
simulation_config = SimulationConfig(duration=8000)
job = qmm.simulate(config, test_prog, simulation_config)
fig = plot_simulator_output([["RF"],["qubit"]], job, config, duration_ns=8000)
fig.show()
```

## plot_ar_attempts
This function plots the histogram of the number of attempts necessary to perform active reset.

### Usage example

```python

```
