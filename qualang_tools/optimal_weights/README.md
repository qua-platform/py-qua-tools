# Readout optimal integration weights

In the dispersive readout of a superconducting qubit, a microwave pulse is sent to the readout
resonator and the reflected or transmitted signal is captured and analyzed to infer the 
state of the qubit.

The steps to capture the state of the qubit are: (i) capture the analog signal coming out of the resonator,
(ii) demodulation of the analog signal, and (iii) the integration of the demodulated signal. 

The integration step can be done with a constant weights to all data points of the captured signal,
nevertheless, the signal coming out of the resonator is not constant and has time dynamics. Thus, non-constant
integration weights could be exploited to maximize the amount of information extracted from a readout operation.

The resonator coupled to a qubit has a time dynamic that is dependent on three parameters: 
the power, the dispersive shift $\chi$, and the loss $\kappa$.

The following figure shows the simulated I and Q trajectories of the ground and excited states as a function of time
and in the IQ-plane,

![traject](Fig1_trajectory.png)

The optimal integration weights can be obtained by capturing the time traces shown above. The optimal integration
weights are the difference between the I and Q traces of the ground and excited state dynamics.

This folder contains five different python files `StateDiscriminator.py`, `TimeDiffCalibrator.py`,
`TwoStateDiscriminator.py`, `configuration.py`, and `ge_discriminator_train_n_benchmark.py`

The `configuration.py` and `ge_discriminator_train_n_benchmark.py` are for pedagogic purposes only. In the
case that you were going to use the `StateDiscriminator.py`, `TimeDiffCalibrator.py`, and `TwoStateDiscriminator.py`
in you experiments you would need your relevant **configuration** file that creates the correct **quantum machine**. Also,
`ge_discriminator_train_n_benchmark.py` need to be small modifications.

## Usage of the optimal weights scripts

First, one needs to define the `discriminator`,

```python
lsb = True
rr_qe = 'rr1a'
qmm = QuantumMachinesManager()
discriminator = TwoStateDiscriminator(qmm=qmm,
                                      config=config,
                                      update_tof=False,
                                      rr_qe=rr_qe,
                                      path=f'ge_disc_params_{rr_qe}.npz',
                                      lsb=lsb)
```

The `discriminator = TwoStateDiscriminator()` requires a Quantum Machines Manager `qmm`, a configuration `config`,
the resonator element `rr_qe`, a path if predefined integration weights were to be used, and `lsb`.

The `lsb` term is related to the *sign* in the signal after the upconversion mixer for the resonator readout. If `lsb=True`,
then the frequency send to the device is `$\omega_{LO}$ - $\omega_{IF}$`, and if `lsb=False`, then the signal is at
`$\omega_{LO}$ + $\omega_{IF}$`.

The code to be used during the training for the weights is,

```python
with program() as training_program:
    n = declare(int)
    I = declare(fixed)
    Q = declare(fixed, value=0)
    I1 = declare(fixed)
    Q1 = declare(fixed)
    I2 = declare(fixed)
    Q2 = declare(fixed)

    I_st = declare_stream()
    Q_st = declare_stream()
    adc_st = declare_stream(adc_trace=True)
    
    with for_(n, 0, n < N, n + 1):
        wait(wait_time, rr_qe)
        training_measurement("readout_pulse_g", use_opt_weights=use_opt_weights)
        save(I, I_st)
        save(Q, Q_st)

        wait(wait_time, rr_qe)
        training_measurement("readout_pulse_e", use_opt_weights=use_opt_weights)
        save(I, I_st)
        save(Q, Q_st)

    with stream_processing():
        I_st.save_all('I')
        Q_st.save_all('Q')
        adc_st.input1().with_timestamps().save_all("adc1")
        adc_st.input2().save_all("adc2")
```

Note that this segment of code is for simulation purposes and can only be used as an inspiration.
Briefly, the QUA program repeats measurements **N** times, and performs measurements for the ground
and excited state. After each measurement `I`, `Q`, and `adc_st` are collected and analyzed by the `TwoStateDiscriminator.py`.

The `TwoStateDiscriminator.py` inherits many properties from the `StateDiscriminator.py`. The
discriminator will perform demodulation of the collected time traces, it has the ability to
apply a digital filter to the measured data, and also there is the possibility post-analyzing the
measured `I` and `Q` values with three different methods `gmm`, `robust`, and `none` (these can be found
inside of `def _get_traces`).

The discriminator will save the optimal weights in an `.npz` file for later usages.

In the QUA code below we can see the direct usage of the discriminator,

```python
with program() as benchmark_readout:
    n = declare(int)
    res = declare(bool)
    I = declare(fixed)
    Q = declare(fixed)

    res_st = declare_stream()
    I_st = declare_stream()
    Q_st = declare_stream()

    with for_(n, 0, n < N, n + 1):
        wait(wait_time, rr_qe)
        discriminator.measure_state("readout_pulse_g", "out1", "out2", res, I=I, Q=Q)
        save(res, res_st)
        save(I, I_st)
        save(Q, Q_st)

        wait(wait_time, rr_qe)
        discriminator.measure_state("readout_pulse_e", "out1", "out2", res, I=I, Q=Q)
        save(res, res_st)
        save(I, I_st)
        save(Q, Q_st)

        seq0 = [0, 1] * N

    with stream_processing():
        res_st.save_all('res')
        I_st.save_all('I')
        Q_st.save_all('Q')
```

The function `discriminator.measure_state` is directly used to perform a measurement having
previously trained the discriminator.