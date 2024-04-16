# Results tools
This library includes tools to help handling results from QUA programs.

## fetching_tool
The fetching tool has an API to easily fetch data from the stream processing.

First the results handle needs to be initiated by specifying the QM job and the list of data to be fetched. 
These values must correspond to results saved in the stream processing. A flag is also avalable with two options:
- `mode="wait_for_all"` will wait until all values were processed for all named results before fetching.
- `mode="live"` will fetch data one by one for all named results for live plotting purposes.

Then the results can be fetched with the `.fetch_all()` method while the program is processing, as shown in the code snippet below.

### Usage example
 
```python
from qualang_tools.results import fetching_tool

n_avg = 1000
with program() as prog:
    # QUA program with n_avg averaging iterations

qmm = QuantumMachinesManager(host=qop_ip, port=qop_port, cluster_name=cluster_name)
qm = qmm.open_qm(config)
job = qm.execute(prog)

my_results = fetching_tool(job, data_list=["I", "Q", "Ie", "Qe", "Ig", "Qg"], mode="live")

fig = plt.figure()

while my_results.is_processing():
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
from qualang_tools.results import fetching_tool, progress_counter

n_avg = 1000

with program as prog:
    # QUA program with n_avg averaging iterations

qmm = QuantumMachinesManager()
qm = qmm.open_qm(config)
job = qm.execute(prog)

my_results = fetching_tool(job, data_list=["iteration", "I", "Q", "Ie", "Qe", "Ig", "Qg"], mode="live")

fig = plt.figure()

while my_results.is_processing():
    # Live plotting
    iteration, I, Q, Ie, Qe, Ig, Qg = my_results.fetch_all()
    progress_counter(iteration, n_avg, start_time=my_results.get_start_time())
    ...
```

## wait_until_job_is_paused
This function makes the Python console wait until the OPX reaches a "pause" statement.

It is used when the OPX sequence needs to be synchronized with an external parameter sweep and to ensure that the OPX
sequence is done before proceeding to the next iteration of the external loop, or when using IO variables:
https://docs.quantum-machines.co/0.1/qm-qua-sdk/docs/Guides/features/?h=pause#pause-resume-and-io-variables

### Usage example

The snippet below, shows how to use this function in the case of a wide resonator spectroscopy, where the LO frequency 
is swept with an external LO source in python. 

```python
from qualang_tools.results import progress_counter, wait_until_job_is_paused
from qm.qua import *


with program() as wide_resonator_spec:
    n = declare(int)  # QUA variable for the averaging loop
    i = declare(int)  # QUA variable for the LO frequency sweep
    f = declare(int)  # QUA variable for the qubit frequency
    I = declare(fixed)  # QUA variable for the measured 'I' quadrature
    Q = declare(fixed)  # QUA variable for the measured 'Q' quadrature
    I_st = declare_stream()  # Stream for the 'I' quadrature
    Q_st = declare_stream()  # Stream for the 'Q' quadrature
    n_st = declare_stream()  # Stream for the averaging iteration 'n'

    with for_(i, 0, i < len(freqs_external) + 1, i + 1):
        pause()  # This waits until it is resumed from python
        with for_(n, 0, n < n_avg, n + 1):
            with for_(*from_array(f, frequencies)):
                # Update the frequency of the digital oscillator linked to the qubit element
                update_frequency("resonator", f)
                # Play the readout pulse and measure the state of the resonator
                measure(
                    "readout",
                    "resonator",
                    None,
                    dual_demod.full("cos", "out1", "sin", "out2", I),
                    dual_demod.full("minus_sin", "out1", "cos", "out2", Q),
                )
                # Wait for the qubit to decay to the ground state
                wait(1_000, "resonator")
                # Save the 'I' & 'Q' quadratures to their respective streams
                save(I, I_st)
                save(Q, Q_st)
        # Save the LO iteration to get the progress bar
        save(i, n_st)

    with stream_processing():
        # Cast the data into a 2D matrix, average the matrix along its second dimension (of size 'n_avg') and store the results
        # (1D vector) on the OPX processor
        I_st.buffer(len(frequencies)).buffer(n_avg).map(FUNCTIONS.average()).save_all("I")
        Q_st.buffer(len(frequencies)).buffer(n_avg).map(FUNCTIONS.average()).save_all("Q")
        n_st.save_all("iteration")

# Open the quantum machine manager
qmm = QuantumMachinesManager()
# Open the quantum machine
qm = qmm.open_qm(config)
# Send the QUA program to the OPX, which compiles and executes it. It will stop at the 'pause' statement.
job = qm.execute(wide_resonator_spec)
# Creates results handles to fetch the data
res_handles = job.result_handles
I_handle = res_handles.get("I")
Q_handle = res_handles.get("Q")
n_handle = res_handles.get("iteration")
for i in range(len(freqs_external)):  # Loop over the LO frequencies
    # Set the frequency of the LO source
    ...
    # Resume the QUA program (escape the 'pause' statement)
    job.resume()
    # Wait until the program reaches the 'pause' statement again, indicating that the QUA sequence is done
    wait_until_job_is_paused(job, timeout=60, strict_timeout=True)
    # Wait until the data of this run is processed by the stream processing
    I_handle.wait_for_values(i + 1)
    Q_handle.wait_for_values(i + 1)
    n_handle.wait_for_values(i + 1)
    # Fetch the data from the last OPX run corresponding to the current LO frequency
    I = np.concatenate(I_handle.fetch(i)["value"])
    Q = np.concatenate(Q_handle.fetch(i)["value"])
    iteration = n_handle.fetch(i)["value"][0]
    # Progress bar
    progress_counter(iteration, len(freqs_external))
    # Process and plot the results
    ...
```


## Data handler
The `DataHandler` is used to easily save data once a measurement has been performed.
It saves data into an automatically generated folder with folder structure:
`{root_data_folder}/%Y-%m-%d/#{idx}_{name}_%H%M%S`.  
- `root_data_folder` is the root folder for all data, defined once at the start
- `%Y-%m-%d`: All datasets are first ordered by date
- `{idx}`: Datasets are identified by an incrementer (starting at `#1`).  
  Whenever a save is performed, the index of the last saved dataset is determined and
  increased by 1.
- `name`: Each data folder has a name
- `%H%M%S`: The time is also specified.
This structure can be changed in `DataHandler.folder_structure`.

Data is generally saved using the command `data_handler.save_data("msmt_name", data)`, 
where `data` is a dictionary.
The data is saved to the json file `data.json` in the data folder, but nonserialisable 
types are saved into separate files. The following nonserialisable types are currently
supported:
- Matplotlib figures
- Numpy arrays
- Xarrays


### Basic example
```python
from qualang_tools.results.data_handler import DataHandler
# Assume a measurement has been performed, and all results are collected here
T1_data = {
    "T1": 5e-6,
    "T1_figure": plt.figure(),
    "IQ_array": np.array([[1, 2, 3], [4, 5, 6]])
}

# Initialize the DataHandler
data_handler = DataHandler(root_data_folder="C:/data")

# Save results
data_folder = data_handler.save_data(data=T1_data, name="T1_measurement")
print(data_folder)
# C:/data/2024-02-24/#152_T1_measurement_095214
# This assumes the save was performed at 2024-02-24 at 09:52:14
```
After calling `data_handler.save_data()`, four files are created in `data_folder`:
- `T1_figure.png`
- `arrays.npz` containing all the numpy arrays
- `data.json` which contains:  
    ```
    {
        "T1": 5e-06,
        "T1_figure": "./T1_figure.png",
        "IQ_array": "./arrays.npz#IQ_array"
    }
    ```
- `node.json` which contains all metadata related to this save.

### Creating a data folder
A data folder can be created in two ways:
```python
from qualang_tools.results.data_handler import DataHandler
# Initialize the DataHandler
data_handler = DataHandler(root_data_folder="C:/data")

# Method 1: explicitly creating data folder
data_folder_properties = data_handler.create_data_folder(name="new_data_folder")

# Method 2: Create when saving results
data_folder = data_handler.save_data(data=T1_data, name="T1_measurement")
```
Note that the methods return different results. 
The method `DataHandler.save_data` simply returns the path to the newly-created data folder, whereas `DataHandler.create_data_folder` returns a dict with additional information on the data folder such as the `idx`.
This additional information can also be accessed after calling `DataHandler.save_data` through the attribute `DataHandler.path_properties`.

### Saving multiple times
A `DataHandler` object can be used to save multiple times to different data folders:
```python
from qualang_tools.results.data_handler import DataHandler
# Initialize the DataHandler
data_handler = DataHandler(root_data_folder="C:/data")

T1_data = {...}

# Save results
data_folder = data_handler.save_data(data=T1_data, name="T1_measurement")
# C:/data/2024-02-24/#1_T1_measurement_095214

T1_modified_data = {...}

data_folder = data_handler.save_data(data=T1_modified_data, name="T1_measurement")
# C:/data/2024-02-24/#2_T1_measurement_095217
```
The save second call to `DataHandler.save_data` creates a new data folder where the incrementer is increased by 1.

### Manually adding additional files to data folder
After a data folder has been created, its path can be accessed from `DataHandler.path`.  
This allows you to add additional files:

```python
data_folder = data_handler.save_data(data)
assert data_folder == data_handler.path  # data_folder is added to data_handler.path

(data_handler.path / "test_file.txt").write_text("I'm adding a file to the data folder")
```

### Auto-saving additional files to data folder
In many cases certain files need to be added every time a data folder is created.
Instead of having to manually add these files each time, they can be specified beforehand:

```python
DataHandler.additional_files = {
    "configuration.py": "configuration.py
}
```
Each key is a path from the current working directory, and the corresponding value is the target filepath w.r.t. the data folder. 
The key does not have to be a relative filepath, it can also be an absolute path. 
This can be useful if you want to autosave a specific file on a fixed location somewhere on your hard drive.

### Use filename as name
Instead of manually specifying the name for a data folder, often the current filename is a good choice.
This can be done by creating the data handler as such:

```python
from pathlib import Path
data_handler = DataHandler(name=Path(__file__).stem)
```