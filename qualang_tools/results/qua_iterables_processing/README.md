## fetch_xarray_data

`fetch_xarray_data` fetches results from a completed QUA job and returns them as an [`xarray.Dataset`](https://docs.xarray.dev/en/stable/generated/xarray.Dataset.html), with each result stream automatically shaped and labelled according to the QUA iterables.

It accepts the iterables as either a plain list of `IterableBase` objects or a `QuaProduct` (both are created with qm-qua >= 1.3.1 iterables). The function handles reassembling per-index streams produced by native iterables, and transposes axes so that dimension ordering in the returned Dataset always matches the original iteration order.

**Requirements:** `xarray >= 2024.1`, `qm-qua >= 1.3.1`. On older qm-qua, `fetch_xarray_data` raises a clear `ImportError`; the rest of `qualang_tools` remains importable.

### Basic usage

The simplest way to use `fetch_xarray_data` is to pass your iterables as a plain list — the same list you passed to `QuaProduct` to drive the program:

```python
import numpy as np
from qm.qua import program, declare_with_stream, assign, fixed
from qm.qua.extensions.qua_iterators import (
    QuaProduct, QuaIterableRange, PythonIterable, QuaIterable,
)
from qualang_tools.results import fetch_xarray_data

frequencies = np.linspace(100e6, 200e6, 11)
qubits = ["q1", "q2", "q3"]
n_shots = 100

iterables = [
    QuaIterableRange("shot", n_shots),       # QUA iterable: averaged over on-FPGA if desired
    PythonIterable("qubit", qubits),         # Python iterable: loops in Python
    QuaIterable("frequency", frequencies),   # QUA iterable
]

with program() as prog:
    for args in QuaProduct(iterables):
        I = declare_with_stream(fixed, "I")
        assign(I, args.frequency)            # store something per iteration point

job = qm.execute(prog)
job.result_handles.wait_for_all_values()

ds = fetch_xarray_data(job, iterables)
# ds is an xr.Dataset with a variable "I" of shape (100, 3, 11)
# and coordinates: shot=[0..99], qubit=["q1","q2","q3"], frequency=[100e6..200e6]
print(ds)
```

### Stream averaging

When a stream is declared with `average_axes`, the averaged dimensions are dropped from the returned Dataset. Other streams using the same iterables retain their full dimensionality.

```python
iterables = [
    QuaIterableRange("shot", 100),
    PythonIterable("qubit", ["q1", "q2"]),
    QuaIterable("frequency", np.linspace(100e6, 200e6, 11)),
]

with program() as prog:
    for args in QuaProduct(iterables):
        raw = declare_with_stream(fixed, "I_raw")
        avg = declare_with_stream(float, "I_avg", average_axes=["shot"])
        assign(raw, args.frequency)
        assign(avg, args.frequency)

ds = fetch_xarray_data(job, iterables)
# ds["I_raw"]: dims (shot, qubit, frequency), shape (100, 2, 11)
# ds["I_avg"]: dims (qubit, frequency),        shape (2, 11)  — shot averaged out
```

### Coordinate metadata (units)

Pass a `metadata` dict with a `"unit"` key to any iterable to have that unit attached to the corresponding coordinate in the Dataset:

```python
iterables = [
    QuaIterableRange("shot", 100),
    QuaIterable("frequency", np.linspace(100e6, 200e6, 11), metadata={"unit": "Hz"}),
    PythonIterable("qubit", ["q1", "q2"], metadata={"unit": "qubit_id"}),
]

ds = fetch_xarray_data(job, iterables)
print(ds.coords["frequency"].attrs["unit"])  # "Hz"
```

### Blocking until the job finishes

Pass `wait_until_done=True` to block inside `fetch_xarray_data` rather than waiting manually:

```python
ds = fetch_xarray_data(job, iterables, wait_until_done=True)
```

### QuaZip support

`QuaZip` groups multiple iterables that advance together (zipped, not a full product). The zip group is treated as a single dimension named by the `QuaZip`'s `name` argument:

```python
from qm.qua.extensions.qua_iterators import QuaZip

iterables = [
    QuaIterableRange("shot", 10),
    QuaZip([
        PythonIterable("qubit", ["q1", "q2", "q3"]),
        PythonIterable("flux", [0.1, 0.2, 0.3]),
    ], name="qb_flux"),
    QuaIterable("frequency", frequencies),
]

ds = fetch_xarray_data(job, iterables)
# ds["my_stream"]: dims (shot, qb_flux, frequency), shape (10, 3, 11)
```

### Passing a QuaProduct directly

If you already hold a `QuaProduct` object (e.g. because you constructed it before the program), you can pass it directly — `fetch_xarray_data` accepts either form:

```python
qua_product = QuaProduct([
    QuaIterableRange("shot", n_shots),
    PythonIterable("qubit", qubits),
    QuaIterable("frequency", frequencies),
])

with program() as prog:
    for args in qua_product:
        I = declare_with_stream(fixed, "I")
        assign(I, args.frequency)

ds = fetch_xarray_data(job, qua_product)   # QuaProduct passed directly
```
