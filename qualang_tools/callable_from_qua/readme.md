# Callable from QUA

## Introduction

This module allows the user to define Python functions and call them directly from the core of a QUA program. 
Underneath the hood, a `pause/resume` workflow is implemented for each function and the `stream processing` is used to pass QUA variables directly as arguments of these functions.
Data can also be transferred from the Python functions to the QUA program using `IO variables`.

As shown below, the QUA program needs to be executed within the `local_run()` context manager that has been incorporated to the structure of the QUA program. 
Note that additional Python functions can be executed at each callback for live plotting purposes for instance.

Several use-cases have been envisioned:
* Extract QUA variables and print them while the program is running for debugging purposes.
* Perform feedback protocols where the error signal is corrected with an external instrument (feedback on a charge sensor with a QDAC channel for instance).
* Update different parameters from external instruments (LO frequency/gain, flux bias, magnetic field...) when measuring several qubits sequentially within a Python for loop.

All these use-cases can be found in the [example](../../examples/callable_from_qua/README.md) section.

**Note:** A future release will allow live-plotting, as well as the transfer of array between the Python terminal and the running 
QUA program for more advanced use-cases.

## Usage Example
Very minor modifications of the standard scripts are needed.
1. The execution requires small modifications of the main QUA SDK which will be updated in a future release.
For now, the QUA program object has been patched and the following line must be called prior to using the callable from QUA functions. 
```python
from qualang_tools.callable_from_qua import callable_from_qua, patch_qua_program_addons

# Patch to add the callable from qua functions to the main SDK
patch_qua_program_addons()
```
1. Then the `callable_from_qua` functions need to be defined using the `@callable_from_qua` decorator. There is no limit in the number of `@callable_from_qua` functions.
```python
@callable_from_qua
def set_lo_freq(qm, element, frequency):
    # Here the LO frequency must be passed in kHz instead of Hz, 
    # because the QUA integer ranges in +/-2**31 ~ +/- 2.1e9
    print(f"setting the LO frequency of {element} to {frequency * 1e-3} GHz")
    qm.octave.set_lo_frequency(element, frequency * 1e3)
    qm.octave.set_element_parameters_from_calibration_db(element, qm.get_running_job())

@callable_from_qua
def qua_print(*args):
    text = ""
    for i in range(0, len(args) - 1, 2):
        text += f"{args[i]} = {args[i+1]} | "
    print(text)
```
2. The callable_from_qua functions can be inserted directly in the standard QUA program.
```python
qmm = QuantumMachinesManager()
qm = qmm.open_qm(config)

LOs = np.arange(4.5e9, 7e9, 250e6)  # LO frequencies in Hz
IFs = np.arange(1e6, 251e6, 2e6)  # Intermediate frequencies in Hz
n_avg = 100
with program() as prog:
    n = declare(int)
    f_LO = declare(int)
    f_IF = declare(int)
    I = declare(fixed)
    Q = declare(fixed)
    I_st = declare_stream()
    Q_st = declare_stream()
    # Loop over the LO frequencies in kHz
    with for_(*from_array(f_LO, LOs / 1e3)):
        # Update the LO frequency in Python
        set_lo_freq(qm, "resonator", f_LO)
        # Standard averaging loop
        with for_(n, 0, n < n_avg, n + 1):
            # Loop over the intermediate frequencies
            with for_(*from_array(f_IF, IFs)):
                # Update the intermediate frequency of the readout resonator
                update_frequency("resonator", f_IF)
                # Check the value of the frequencies in Python
                # --> Use only for debugging, because it will slow down the sequence
                qua_print("LO", f_LO, "IF", f_IF)  
                # Measure the readout resonator
                measure(
                    "readout",
                    "resonator",
                    None,
                    dual_demod.full("cos", "out1", "sin", "out2", I),
                    dual_demod.full("minus_sin", "out1", "cos", "out2", Q),
                )
                # Wait for the qubit to decay to the ground state
                wait(1000, "resonator")
                # Save the 'I' & 'Q' quadratures to their respective streams
                save(I, I_st)
                save(Q, Q_st)

    with stream_processing():
        I_st.buffer(len(IFs)).buffer(n_avg).map(FUNCTIONS.average()).buffer(len(LOs)).save("I")
        Q_st.buffer(len(IFs)).buffer(n_avg).map(FUNCTIONS.average()).buffer(len(LOs)).save("Q")
```
4. The QUA program can be executed using the usual `qm.execute` function.
