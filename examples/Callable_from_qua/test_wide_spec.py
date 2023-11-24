from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from configuration_octave import *
import matplotlib.pyplot as plt
import warnings
from qualang_tools.loops import from_array
from qualang_tools.units import unit
warnings.filterwarnings("ignore")

from callable_from_qua import program, run_local

u = unit()

def get_LOs(fstart, fend, intermediate_frequencies=()):
    first_LO = fstart - intermediate_frequencies[0]
    last_LO =  fend - intermediate_frequencies[-1]
    step_LO = intermediate_frequencies[-1] - intermediate_frequencies[0]

    LOs = np.arange(first_LO, last_LO+0.1, step_LO)
    ftot = np.concatenate([LO + intermediate_frequencies for LO in LOs])
    return LOs, ftot

IFs = np.linspace(1e6, 251e6, 101)
LOs, ftot = get_LOs(4.501e9, 6.75e9, IFs)
config["elements"]["qubit"]["intermediate_frequency"] = IFs[len(IFs)//2]

qmm = QuantumMachinesManager(host="172.16.33.101", cluster_name="Cluster_81",octave=octave_config)
qm = qmm.open_qm(config)


@run_local
def set_lo_freq(qm, value):
    lo_freq = value * 1e3
    print(f"setting LO to {lo_freq*1e-9} GHz")
    qm.octave.set_lo_frequency("qubit", lo_freq)
    qm.octave.set_element_parameters_from_calibration_db("qubit", qm.get_running_job())


with program() as prog:
    n_avg = 100
    n = declare(int)
    f_LO = declare(int)
    f_IF = declare(int)
    I = declare(fixed)
    Q = declare(fixed)
    I_st = declare_stream()
    Q_st = declare_stream()
    with for_(*from_array(f_LO, LOs / 1e3)):
        set_lo_freq(qm=qm, value=f_LO)
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
        # I_st.buffer(len(IFs)).buffer(n_avg).map(FUNCTIONS.average()).buffer(len(LOs)).save("I")
        # Q_st.buffer(len(IFs)).buffer(n_avg).map(FUNCTIONS.average()).buffer(len(LOs)).save("Q")
        I_st.buffer(len(IFs)).buffer(n_avg).map(FUNCTIONS.average()).save_all("I")
        Q_st.buffer(len(IFs)).buffer(n_avg).map(FUNCTIONS.average()).save_all("Q")


# def my_prog(callables_from_qua, qm):
#     n_avg = 1000
#     n = declare(int)
#     f_LO = declare(int)
#     with for_(*from_array(f_LO, LOs / 1e3)):
#         update_frequency("qubit", 126e6)
#         set_lo_freq(batches=callables_from_qua, qm=qm, value=f_LO, intermediate_frequency=126e6)
#         with for_(n, 0, n < n_avg, n + 1):
#             play("cw"*amp(0), "qubit", duration=1_000_000)



# Calibrate all LOs
def calibrate_several_LOs(element, lo_frequencies, mean_if_frequency):
    for lo in lo_frequencies:
        qm.calibrate_element(element, {lo: [mean_if_frequency]})
# calibrate_several_LOs("qubit", LOs, IFs[len(IFs)//2])

fig = plt.figure()
def live_plot(res_handles):
    count = res_handles.get("I").count_so_far()
    if count > 0:
        I = -res_handles.get("I").fetch_all()["value"][count-1] * 2**12 / readout_len
        Q = -res_handles.get("Q").fetch_all()["value"][count-1] * 2**12 / readout_len

        plt.subplot(211)
        plt.plot((LOs[count-1]+IFs)/u.MHz,I)
        plt.ylabel("I quadrature [V]")
        plt.xlabel("Frequency [MHz]")
        plt.subplot(212)
        plt.plot((LOs[count-1]+IFs)/u.MHz, Q)
        plt.ylabel("Q quadrature [V]")
        plt.xlabel("Frequency [MHz]")
        plt.tight_layout()
        plt.pause(0.01)

# Execute the QUA program using the callable from QUA framework
with prog.local_run(qm, [live_plot]):
    job = qm.execute(prog)

