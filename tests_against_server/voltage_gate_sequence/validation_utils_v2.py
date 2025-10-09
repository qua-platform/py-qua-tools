from configuration import *

from qm import SimulationConfig, QuantumMachinesManager
from qm_saas import QOPVersion, QmSaas
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go


def simulate_program(prog, mode: str = "station", simulation_duration=10000):
    if mode == "cloud":
        email = ""
        password = ""

        dev = True

        if dev:
            host = "qm-saas.dev.quantum-machines.co"
        else:
            host = "qm-saas.quantum-machines.co"

        # Initialize QOP simulator client
        client = QmSaas(email=email, password=password, host=host)

        version = QOPVersion(client.latest_version().name)  # Specify the QOP version

        with client.simulator(version) as instance:
            # Initialize QuantumMachinesManager with the simulation instance details
            qmm = QuantumMachinesManager(
                host=instance.host, port=instance.port, connection_headers=instance.default_connection_headers
            )
            # Simulates the QUA program for the specified duration
            simulation_config = SimulationConfig(duration=simulation_duration // 4)  # In clock cycles = 4ns
            # Simulate blocks python until the simulation is done
            job = qmm.simulate(config, prog, simulation_config)
            # Get the simulated samples
            samples = job.get_simulated_samples()

    elif mode == "station":
        # Connect to QMM
        qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name)
        # Simulates the QUA program for the specified duration
        simulation_config = SimulationConfig(duration=simulation_duration // 4)  # In clock cycles = 4ns
        # Simulate blocks python until the simulation is done
        job = qmm.simulate(config, prog, simulation_config)
        # Get the simulated samples
        samples = job.get_simulated_samples()

    return qmm, samples


def validate_program(samples, requested_wf_p, requested_wf_m):
    t0 = np.where(samples["con1"].analog[f"{fem}-{port_P1}"] != 0)[0][0]
    wf_p = samples["con1"].analog[f"{fem}-{port_P1}"][t0:]
    wf_m = samples["con1"].analog[f"{fem}-{port_P2}"][t0:]
    t1 = np.where(wf_p == 0)[0][0]
    # Plot the simulated samples
    plt.figure()
    plt.plot(requested_wf_p, "bx", label="requested wf (+)")
    plt.plot(wf_p[: t1 + 1], "b", label="simulated wf (+)")
    plt.plot(requested_wf_m, "rx", label="requested wf (-)")
    plt.plot(wf_m[: t1 + 1], "r", label="simulated wf (-)")
    plt.legend()
    print(
        f"Difference between requested and simulated (+): {np.mean((wf_p[:len(requested_wf_p)] - requested_wf_p) / requested_wf_p) * 100:.2e} %"
    )
    print(
        f"Difference between requested and simulated (-): {np.mean((wf_m[:len(requested_wf_m)] - requested_wf_m) / requested_wf_m) * 100:.2e} %"
    )
    print(
        f"Relative sum after compensation (+): {np.sum(wf_p[:t1+1]) / np.sum(wf_p[:len(requested_wf_p)]) * 100:.2f} %"
    )
    print(
        f"Relative sum after compensation (-): {np.sum(wf_m[:t1+1]) / np.sum(wf_p[:len(requested_wf_m)]) * 100:.2f} %"
    )
    print(f"Max gradient during compensation (+): {max(np.diff(wf_p[:t1+1])) * 1000:.2f} mV")
    print(f"Max gradient during compensation (-): {max(np.diff(wf_m[:t1+1])) * 1000:.2f} mV")
    # Success criteria
    assert (np.mean((wf_p[: len(requested_wf_p)] - requested_wf_p) / requested_wf_p) < 0.1) & (
        np.mean((wf_m[: len(requested_wf_m)] - requested_wf_m) / requested_wf_m) < 0.1
    ), "Simulated wf doesn't match requested wf."
    assert (np.sum(wf_p[: t1 + 1]) / np.sum(wf_p[: len(requested_wf_p)]) * 100 < 1) & (
        np.sum(wf_m[: t1 + 1]) / np.sum(wf_p[: len(requested_wf_m)]) * 100 < 1
    ), "The compensation pulse leads to more than 1% error."
    assert (max(np.abs(np.diff(wf_p[: t1 + 1]))) < 0.5) & (
        max(np.abs(np.diff(wf_m[: t1 + 1]))) < 0.5
    ), "The maximum voltage gradient is above 0.5 V."

def validate_program_v2(samples, requested_wf_p, requested_wf_m, time = None):
    t_pulse = len(requested_wf_p)
    wf_p = samples["con1"].analog[f"{fem}-{port_P1}"]
    wf_m = samples["con1"].analog[f"{fem}-{port_P2}"]
    temp = np.where(wf_p != 0)
    if len(temp[0])>0:
        t0_p = temp[0][0]
    else:
        t0_p = len(wf_p)
    temp = np.where(wf_m != 0)
    if len(temp[0])>0:
        t0_m = temp[0][0]
    else:
        t0_m = len(wf_m)
    t0 = min(t0_p, t0_m)
    wf_p = samples["con1"].analog[f"{fem}-{port_P1}"][t0:]
    wf_m = samples["con1"].analog[f"{fem}-{port_P2}"][t0:]
    
    if time:
        wf_p = wf_p[:time]
        wf_m = wf_m[:time]
    
    wf_p = np.concatenate(([0], wf_p))
    wf_m = np.concatenate(([0], wf_m))
    x = np.linspace(0, len(wf_p)-1, len(wf_p))

    # Plot the simulated samples
    fig = go.Figure()

    # Requested wf (+) — blue X
    fig.add_trace(go.Scatter(
        y=requested_wf_p,
        mode='markers',
        marker=dict(color='blue', symbol='circle', size=4),
        name='requested wf (+)'
    ))

    # Simulated wf (+) — blue line
    fig.add_trace(go.Scatter(
        y=wf_p,
        mode='lines',
        line=dict(color='blue'),
        name='simulated wf (+)'
    ))

    # Requested wf (-) — red X
    fig.add_trace(go.Scatter(
        y=requested_wf_m,
        mode='markers',
        marker=dict(color='red', symbol='circle', size=4),
        name='requested wf (-)'
    ))

    # Simulated wf (-) — red line
    fig.add_trace(go.Scatter(
        y=wf_m,
        mode='lines',
        line=dict(color='red'),
        name='simulated wf (-)'
    ))

    # Show legend and interactive figure
    fig.update_layout(
        legend=dict(title='Waveforms'),
        title='Waveform Comparison',
        xaxis_title='Time Index',
        yaxis_title='Amplitude'
    )

    fig.show()

    # calculate errors on p pulse
    diff_p = np.trapz(np.abs(wf_p[:t_pulse] - requested_wf_p), x[:t_pulse]) # area between the curves
    area_p = np.trapz(np.abs(wf_p[:t_pulse]), x[:t_pulse]) # area of the simulated pulse
    area_p_requested = np.trapz(np.abs(requested_wf_p), x[:t_pulse]) # area of the requested pulse
    area_comp_p = np.trapz(wf_p, x) # area of the compensated pulse (sign sensitive)
    
    # calculate errors on m pulse
    diff_m = np.trapz(np.abs(wf_m[:t_pulse] - requested_wf_m), x[:t_pulse]) # area between the curves
    area_m = np.trapz(np.abs(wf_m[:t_pulse]), x[:t_pulse]) # area of the simulated pulse
    area_m_requested = np.trapz(np.abs(requested_wf_m), x[:t_pulse]) # area of the requested pulse
    area_comp_m = np.trapz(wf_m, x) # area of the compensated pulse (sign sensitive)
    
    print(
        f"Difference between requested and simulated (+): {diff_p/area_p * 100:.2e} %"
    )
    print(
        f"Difference between requested and simulated (-): {diff_m/area_m * 100:.2e} %"
    )
    print(
        f"Relative sum after compensation (+): {area_comp_p/area_p * 100:.2f} %"
    )
    print(
        f"Relative sum after compensation (-): {area_comp_m/area_m * 100:.2f} %"
    )
    print(f"Max gradient during compensation (+): {max(np.abs(np.diff(wf_p))) * 1000:.2f} mV")
    print(f"Max gradient during compensation (-): {max(np.abs(np.diff(wf_m))) * 1000:.2f} mV")


def get_linear_ramp(start_value, end_value, duration, sampling_rate=1):
    """
    Generates a list of points describing a linear ramp between two points.

    Args:
        start_value (float): The starting value of the ramp.
        end_value (float): The ending value of the ramp.
        duration (int): The duration of the ramp (in time units).
        sampling_rate (int, optional): Number of samples per time unit. Defaults to 1.

    Returns:
        list: List of float values representing the ramp.
    """
    num_points = duration*sampling_rate
    if num_points.is_integer():
        num_points = int(num_points)
    if num_points <= 1:
        return [start_value] * num_points
    ramp = [start_value + (end_value - start_value) * (i + 1) / (num_points) for i in range(num_points)]
    return ramp

def calculate_voltage_offset(voltage, duration, time_constant):
    """Calculates the voltage adjustment of a compensation ramp to account for decay in a bias tee.

    :param voltage (float): Voltage applied at the start of the step
    :param duration (int): Duration of the step in nanoseconds
    :param time_constant (int): Time constant of the bias tee in nanoseconds
    """
    return voltage * duration / time_constant

def add_to_waveform(waveform, level, duration, ramp_time = 0, sampling_rate=1, time_constant = None, offset = None):
    """
    Generates a list of points describing a pulse (ramp + dwell). Adds the points to the existing pulse.

    Args:
        waveform (list): The existing waveform (can be empty).
        level (float): The voltage level of the pulse segment.
        duration (int): The duration of the pulse segment (in time units).
        sampling_rate (int, optional): Number of samples per time unit. Defaults to 1.
        time_constant (int): The time constant of the bias tee in time units. This causes compensation of the pulse segment.
        offset (list(float)): The voltage offset that exists between the two sides of the bias tee. A list of length 1.

    Returns:
        list: List of float values representing the entire waveform. Since the waveform is a list, it is mutable and will be changed.
    """
    assert ramp_time!=0 or duration!=0, 'The duration and ramp time cannot both be zero.'
    if offset is None:
        offset[0] = 0
    if ramp_time == 0:
        ramp_time = 16
        duration = duration-16
    if len(waveform) == 0:
        waveform[0] = 0.00001
        ramp_time = ramp_time-1/sampling_rate
    waveform += get_linear_ramp(waveform[-1], level + offset[0], ramp_time, sampling_rate)
    dv = 0
    if duration is not 0:
        if time_constant is not None:
            dv = calculate_voltage_offset(waveform[-1], duration, time_constant)
        waveform += get_linear_ramp(waveform[-1], waveform[-1]+dv, duration)
    offset[0] = offset[0] + dv

def plot_pulses(samples, requested_wf_p, requested_wf_m, time = None):
    wf_p = samples["con1"].analog[f"{fem}-{port_P1}"]
    wf_m = samples["con1"].analog[f"{fem}-{port_P2}"]
    temp = np.where(wf_p != 0)
    if len(temp[0])>0:
        t0_p = temp[0][0]
    else:
        t0_p = len(wf_p)
    temp = np.where(wf_m != 0)
    if len(temp[0])>0:
        t0_m = temp[0][0]
    else:
        t0_m = len(wf_m)
    t0 = min(t0_p, t0_m)
    wf_p = samples["con1"].analog[f"{fem}-{port_P1}"][t0:]
    wf_m = samples["con1"].analog[f"{fem}-{port_P2}"][t0:]
    
    if time:
        wf_p = wf_p[:time]
        wf_m = wf_m[:time]
    
    wf_p = np.concatenate(([0], wf_p))
    wf_m = np.concatenate(([0], wf_m))

    # Plot the simulated samples
    fig = go.Figure()

    # Requested wf (+) — blue X
    fig.add_trace(go.Scatter(
        y=requested_wf_p,
        mode='markers',
        marker=dict(color='blue', symbol='circle', size=4),
        name='requested wf (+)'
    ))

    # Simulated wf (+) — blue line
    fig.add_trace(go.Scatter(
        y=wf_p,
        mode='lines',
        line=dict(color='blue'),
        name='simulated wf (+)'
    ))

    # Requested wf (-) — red X
    fig.add_trace(go.Scatter(
        y=requested_wf_m,
        mode='markers',
        marker=dict(color='red', symbol='circle', size=4),
        name='requested wf (-)'
    ))

    # Simulated wf (-) — red line
    fig.add_trace(go.Scatter(
        y=wf_m,
        mode='lines',
        line=dict(color='red'),
        name='simulated wf (-)'
    ))

    # Show legend and interactive figure
    fig.update_layout(
        legend=dict(title='Waveforms'),
        title='Waveform Comparison',
        xaxis_title='Time Index',
        yaxis_title='Amplitude'
    )

    fig.show()
