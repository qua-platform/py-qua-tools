import time

import pytest
from qualang_tools.addons.calibration.calibrations import u
from qualang_tools.macros.long_wait import long_wait, MAX_WAIT
from qm.qua import *
from qm import SimulationConfig, LoopbackInterface


def test_long_wait_time_live(qmm, config):
    """ Tests that the program runs and finishes without crashing. """
    op = "playOp"

    wait_time = u.to_clock_cycles(30e9)  # 50s
    assert wait_time > MAX_WAIT  # to prove this is truly a long wait

    with program() as prog:
        play(op, "qe1")  # very short pulse
        long_wait(wait_time)

    job = execute_program(qmm, config, prog, simulate=False)

    runtime = 0
    is_running = True

    # calculate runtime
    while is_running:
        start = time.time()
        is_running = job._is_job_running()
        end = time.time()

        # count every 2s, accounting for the call time of _is_job_running()
        call_time = end - start
        runtime += 2
        time.sleep(2 - call_time)

    assert runtime / 4 == wait_time / 1e9


# small wait threshold to verify behaviour at MAX_WAIT without having to simulate that far
dummy_max_wait_time = 200  # clock cycles


@pytest.mark.parametrize("wait_time", [4, 16, 100,
                                       dummy_max_wait_time-1,
                                       dummy_max_wait_time,
                                       dummy_max_wait_time+1,
                                       100*dummy_max_wait_time])
def test_long_wait_time_simulation(qmm, config, wait_time):
    """ Extracts the wait time from simulation and asserts it to be equal to the input wait time."""
    op = "playOp"

    with program() as prog:
        play(op, "qe1")
        long_wait(wait_time, threshold_for_looping=dummy_max_wait_time)
        play(op, "qe1")

    element = config['elements']['qe1']
    pulse = config['pulses'][element['operations'][op]]
    pulse_length = pulse['length']
    pulse_amplitude = config['waveforms'][pulse['waveforms']['single']]['sample']

    job = execute_program(qmm, config, prog, simulate=True, simulation_duration=wait_time + 2*pulse_length + 100)

    output = job.get_simulated_samples().con1.analog['1-1']

    th = pulse_amplitude / 2  # edge threshold
    rising_edges = np.where((output[:-1] <= th/2) & (output[1:] > th/2))[0]
    falling_edges = np.where((output[:-1] > th/2) & (output[1:] <= th/2))[0]

    # in a square -> wait -> square program, the wait time lies between the first falling edge
    # and the second rising edge of the entire program.
    wait_samples = output[falling_edges[0]:rising_edges[1]]

    # plt.plot(output)
    # plt.axvline(falling_edges[0], linestyle='--')
    # plt.axvline(rising_edges[1], linestyle='--')
    # plt.show()

    assert len(wait_samples) == wait_time * u.clock_cycle


def execute_program(qmm, config, prog, simulate=True, simulation_duration=10_000):
    if simulate:
        job = qmm.simulate(
            config,
            prog,
            SimulationConfig(
                simulation_duration,
                simulation_interface=LoopbackInterface([("con1", 1, "con1", 1)]),
                include_analog_waveforms=True,
            ),
        )
    else:
        qm = qmm.open_qm(config)
        job = qm.execute(prog)

    return job
