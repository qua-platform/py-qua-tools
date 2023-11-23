from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import SimulationConfig
from configuration_octave import *
import matplotlib.pyplot as plt
import warnings
from time import sleep
from qm import generate_qua_script
from qualang_tools.loops import from_array
from qualang_tools.units import unit
warnings.filterwarnings("ignore")

from callable_from_qua2 import CallableFromQUA, run_local
import json
from pprint import pprint
# %% Qua program

u = unit()

# IQ imbalance matrix
def IQ_imbalance(g, phi):
    """
    Creates the correction matrix for the mixer imbalance caused by the gain and phase imbalances, more information can
    be seen here:
    https://docs.qualang.io/libs/examples/mixer-calibration/#non-ideal-mixer
    :param g: relative gain imbalance between the 'I' & 'Q' ports. (unit-less), set to 0 for no gain imbalance.
    :param phi: relative phase imbalance between the 'I' & 'Q' ports (radians), set to 0 for no phase imbalance.
    """
    c = np.cos(phi)
    s = np.sin(phi)
    N = 1 / ((1 - g**2) * (2 * c**2 - 1))
    return [float(N * x) for x in [(1 - g) * c, (1 + g) * s, (1 - g) * s, (1 + g) * c]]


def get_calibration_parameters(database, lo_frequency, intermediate_frequency):
    with open(database) as f:
        data = json.load(f)
        for id in data["lo_modes"]:
            if data["lo_modes"][id]["lo_freq"] == lo_frequency:
                timestamp = None
                for lo_id in data["lo_cal"]:
                    if str(data["lo_cal"][lo_id]["lo_mode_id"]) == id:
                        if timestamp is None or timestamp<data["lo_cal"][lo_id]["timestamp"]:
                            i0 = data["lo_cal"][id]["i0"]
                            q0 = data["lo_cal"][id]["q0"]
                            gain = data["lo_cal"][id]["dc_gain"]
                            phase = data["lo_cal"][id]["dc_phase"]
                            timestamp = data["lo_cal"][lo_id]["timestamp"]
                for if_id in data["if_modes"]:
                    if str(data["if_modes"][if_id]["lo_mode_id"]) == id:
                        if data["if_modes"][if_id]["if_freq"] == intermediate_frequency:
                            timestamp = None
                            for if_id2 in data["if_cal"]:
                                if str(data["if_cal"][if_id2]["if_mode_id"]) == id:
                                    if timestamp is None or timestamp < data["if_cal"][if_id2]["timestamp"]:
                                        gain = data["if_cal"][if_id2]["gain"]
                                        phase = data["if_cal"][if_id2]["phase"]
                                        timestamp = data["if_cal"][if_id2]["timestamp"]
                            return i0, q0, gain, phase
                print(f"No data for the intermediate frequency = {intermediate_frequency} Hz is found.")
                return i0, q0, gain, phase
    print(f"No calibration parameters found for (LO, IF) = ({lo_frequency}, {intermediate_frequency})")

@run_local
def set_lo_freq(qm, value, intermediate_frequency):
    lo_freq = value * 1e3
    print(f"setting LO to {lo_freq*1e-9} GHz")
    qm.octave.set_lo_frequency("qubit", lo_freq)
    i0, q0, gain, phase = get_calibration_parameters("calibration_db.json", lo_freq, intermediate_frequency)
    print(f"Updating calibration parameters for (LO, IF) = ({lo_freq*1e-6:0f}, {IFs[len(IFs)//2]*1e-6}) MHz\n"
          f"with i0 = {i0*1e3:.2f} mV, q0 = {q0*1e3:.2f} mV, g = {gain:.4f} & phase = {phase:.3f}")
    qm.set_output_dc_offset_by_element("qubit", "I", i0)
    qm.set_output_dc_offset_by_element("qubit", "Q", q0)
    qm.get_running_job().set_element_correction("qubit", IQ_imbalance(gain, phase))
    sleep(1)


def get_LOs(fstart, fend, intermediate_frequencies=()):
    first_LO = fstart - intermediate_frequencies[0]
    last_LO =  fend - intermediate_frequencies[-1]
    step_LO = intermediate_frequencies[-1] - intermediate_frequencies[0]

    LOs = np.arange(first_LO, last_LO+0.1, step_LO)
    ftot = np.concatenate([LO + intermediate_frequencies for LO in LOs])
    return LOs, ftot


IFs = np.linspace(1e6, 251e6, 101)
LOs, ftot = get_LOs(4.501e9, 6.75e9, IFs)

def my_prog(callables_from_qua, qm):  # TODO: no program() scope
    n_avg = 100
    n = declare(int)
    f_LO = declare(int)
    f_IF = declare(int)
    I = declare(fixed)
    Q = declare(fixed)
    I_st = declare_stream()
    Q_st = declare_stream()
    with for_(*from_array(f_LO, LOs / 1e3)):
        set_lo_freq(batches=callables_from_qua, qm=qm, value=f_LO, intermediate_frequency=IFs[len(IFs)//2])
        with for_(n, 0, n < n_avg, n + 1):
            with for_(*from_array(f_IF, IFs)):
                update_frequency("qubit", f_IF)
                align()
                play("cw", "qubit", duration=100000)
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


def my_prog(callables_from_qua, qm):
    n_avg = 1000
    n = declare(int)
    f_LO = declare(int)
    with for_(*from_array(f_LO, LOs / 1e3)):
        update_frequency("qubit", 126e6)
        set_lo_freq(batches=callables_from_qua, qm=qm, value=f_LO, intermediate_frequency=126e6)
        with for_(n, 0, n < n_avg, n + 1):
            play("cw", "qubit", duration=1_000_000)


def build_prog(callables_from_qua, sequence):  # TODO: behind the scene
    with program() as prog:
        callables_from_qua.declare_all()
        sequence(callables_from_qua, qm)
        callables_from_qua.do_stream_processing()
    return prog


batches = CallableFromQUA()
qmm = QuantumMachinesManager(host="172.16.33.101", cluster_name="Cluster_81",octave=octave_config)
qm = qmm.open_qm(config)

# Calibrate all LOs
def calibrate_several_LOs(element, lo_frequencies, mean_if_frequency):
    for lo in lo_frequencies:
        qm.calibrate_element(element, {lo: [mean_if_frequency]})


# calibrate_several_LOs("qubit", LOs, IFs[len(IFs)//2])
prog = build_prog(batches, my_prog)
job = batches.execute(qm, prog)
# job = qm.execute(prog)

print(generate_qua_script(prog, config)[:1000])
print(-job.result_handles.get("I").fetch_all() * 2**12 / readout_len)
plt.plot(ftot,np.concatenate(-job.result_handles.get("I").fetch_all() * 2**12 / readout_len))
