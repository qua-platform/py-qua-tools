# Plot tools
This library includes tools to help handling plots from QUA programs.

## interrupt_on_close
This function allows to interrupt the execution and free the console when closing the live-plotting figure.

### Usage example

```python
from qualang_tools.plot import interrupt_on_close

qmm = QuantumMachinesManager()
qm = qmm.open_qm(config)
job = qm.execute(cryoscope)

fig = plt.figure(figsize=(15, 15))
interrupt_on_close(fig, job)

while job.result_handles.is_processing():
    # Live plotting
    ...
    # The execution will be cleanly interrupted by closing the figure
```
