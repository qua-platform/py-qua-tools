from configuration import *

from qm import SimulationConfig, QuantumMachinesManager
from qm_saas import QOPVersion, QmSaas
import matplotlib.pyplot as plt
import numpy as np


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
    num_points = duration
    if num_points <= 1:
        return [start_value] * num_points
    ramp = [start_value + (end_value - start_value) * (i + 1) / num_points for i in range(num_points)]
    return [point for point in ramp for _ in range(sampling_rate)]
