# Results tools
This library includes tools to help handling results from QUA programs.

## fetching_tool
The fetching tool has an API to easily fetch data from the stream processing.

First the results handle needs to be initiated by specifying the QM job and the list of data to be fetched. 
These values must correspond to results saved in the stream processing. A flag is also avalable with two options:
- `flag="wait_for_all"` will wait until all values were processed for all named results before fetching.
- `flag="live"` will fetch data one by one for all named results for live plotting purposes.

### Usage example

 
```python
from qualang_tools.results import result_tool

qmm = QuantumMachinesManager()
qm = qmm.open_qm(config)
job = qm.execute(cryoscope)

my_results = result_tool(job, data_list=["I", "Q", "Ie", "Qe", "Ig", "Qg"], flag="live")

fig = plt.figure(figsize=(15, 15))

while job.result_handles.is_processing():
    # Live plotting
    I, Q, Ie, Qe, Ig, Qg = my_results.fetch_all()
    ...
```

## progress_counter
This function displays a progress bar and prints the current progress percentage and remaining computation time.
Several flags are available to customize the progress bar:
- `progress_bar=True`: displays the progress bar if True.
- `percent=True`: displays the progress percentage if True.
- `start_time=None`: displays elapsed time from start if not None.


<img src="progress_bar.PNG" alt="drawing"/>

### Usage example

```python
from qualang_tools.results import result_tool, progress_counter
import time

n_avg = 1000

with program as prog:
    # QUA program with n_avg averaging iterations

qmm = QuantumMachinesManager()
qm = qmm.open_qm(config)
job = qm.execute(cryoscope)

my_results = result_tool(job, data_list=["iteration", "I", "Q", "Ie", "Qe", "Ig", "Qg"], flag="live")

fig = plt.figure(figsize=(15, 15))

t0 = time.time()
while job.result_handles.is_processing():
    # Live plotting
    iteration, I, Q, Ie, Qe, Ig, Qg = my_results.fetch_all()
    progress_counter(iteration, n_avg, start_time=t0)
    ...
```
