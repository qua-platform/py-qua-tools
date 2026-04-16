## fetch_xarray_data

`fetch_xarray_data` fetches results from a completed QUA job and returns them as an [`xarray.Dataset`](https://docs.xarray.dev/en/stable/generated/xarray.Dataset.html), with each result stream automatically shaped and labelled according to the sweep dimensions.

It accepts the sweep as either a plain list of iterables or a `QuaProduct` (both are created with qm-qua >= 1.3.0 iterables). The function handles reassembling per-index streams produced by native iterables, and transposes axes so that dimension ordering in the returned Dataset always matches the original sweep order.

**Requirements:** `xarray >= 2024.1`, `qm-qua >= 1.3.0`

### Basic usage

The simplest way to use `fetch_xarray_data` is to pass your sweep as a plain list of iterables — the same list you passed to `QuaProduct` to drive the program:

```python
import numpy as np
from qm.qua import program, declare_with_stream, assign, fixed
from qm.qua.extensions.qua_iterators import (
    QuaProduct, QuaIterableRange, NativeIterable, QuaIterable,
)
from qualang_tools.loops.qua_iterable_postprocess import fetch_xarray_data

frequencies = np.linspace(100e6, 200e6, 11)
qubits = ["q1", "q2", "q3"]
n_shots = 100

sweep = [
    QuaIterableRange("shot", n_shots),       # QUA iterable: averaged over on-FPGA if desired
    NativeIterable("qubit", qubits),         # native iterable: loops in Python
    QuaIterable("frequency", frequencies),   # QUA iterable
]

with program() as prog:
    for args in QuaProduct(sweep):
        I = declare_with_stream(fixed, "I")
        assign(I, args.frequency)            # store something per sweep point

job = qm.execute(prog)
job.result_handles.wait_for_all_values()

ds = fetch_xarray_data(job, sweep)
# ds is an xr.Dataset with a variable "I" of shape (100, 3, 11)
# and coordinates: shot=[0..99], qubit=["q1","q2","q3"], frequency=[100e6..200e6]
print(ds)
```

### Stream averaging

When a stream is declared with `average_axes`, the averaged dimensions are dropped from the returned Dataset. Other streams in the same sweep retain their full dimensionality.

```python
sweep = [
    QuaIterableRange("shot", 100),
    NativeIterable("qubit", ["q1", "q2"]),
    QuaIterable("frequency", np.linspace(100e6, 200e6, 11)),
]

with program() as prog:
    for args in QuaProduct(sweep):
        raw = declare_with_stream(fixed, "I_raw")
        avg = declare_with_stream(float, "I_avg", average_axes=["shot"])
        assign(raw, args.frequency)
        assign(avg, args.frequency)

ds = fetch_xarray_data(job, sweep)
# ds["I_raw"]: dims (shot, qubit, frequency), shape (100, 2, 11)
# ds["I_avg"]: dims (qubit, frequency),        shape (2, 11)  — shot averaged out
```

### Coordinate metadata (units)

Pass a `metadata` dict with a `"unit"` key to any iterable to have that unit attached to the corresponding coordinate in the Dataset:

```python
sweep = [
    QuaIterableRange("shot", 100),
    QuaIterable("frequency", np.linspace(100e6, 200e6, 11), metadata={"unit": "Hz"}),
    NativeIterable("qubit", ["q1", "q2"], metadata={"unit": "qubit_id"}),
]

ds = fetch_xarray_data(job, sweep)
print(ds.coords["frequency"].attrs["unit"])  # "Hz"
```

### Blocking until the job finishes

Pass `wait_until_done=True` to block inside `fetch_xarray_data` rather than waiting manually:

```python
ds = fetch_xarray_data(job, sweep, wait_until_done=True)
```

### QuaZip support

`QuaZip` groups multiple iterables that advance together (zipped, not a full product). The zip group is treated as a single dimension named by the `QuaZip`'s `name` argument:

```python
from qm.qua.extensions.qua_iterators import QuaZip

sweep = [
    QuaIterableRange("shot", 10),
    QuaZip([
        NativeIterable("qubit", ["q1", "q2", "q3"]),
        NativeIterable("flux", [0.1, 0.2, 0.3]),
    ], name="qb_flux"),
    QuaIterable("frequency", frequencies),
]

ds = fetch_xarray_data(job, sweep)
# ds["my_stream"]: dims (shot, qb_flux, frequency), shape (10, 3, 11)
```

### Passing a QuaProduct directly

If you already hold a `QuaProduct` object (e.g. because you constructed it before the program), you can pass it directly — `fetch_xarray_data` accepts either form:

```python
sweep = QuaProduct([
    QuaIterableRange("shot", n_shots),
    NativeIterable("qubit", qubits),
    QuaIterable("frequency", frequencies),
])

with program() as prog:
    for args in sweep:
        I = declare_with_stream(fixed, "I")
        assign(I, args.frequency)

ds = fetch_xarray_data(job, sweep)   # QuaProduct passed directly
```