# %% Imports
import matplotlib.pylab as plt
from qm.qua import *
from qw_qm_admin import get_machine

from lib.DataCheckExceptions import OutOfSpecException, BadDataException
from lib.batch import BatchJob, BatchProgram, Batch, run_local
from lib.qua_datasets import extract_dict
from lib.quaaxis import QuaAxis
from lib.TempModifications import TempModifications
from qw_qm_admin.quam import QuAM, Qubit

# %% load machine

machine = get_machine()

# %% Parameters

params = {
    "n_avg": 1000,
    "max_mse_in_spec": 1e-05,
    "max_mse_out_of_spec": 0.01,
    "plot": True,
    "fit_data": {}
}


# %% Qua program

@run_local
def set_lo_freq(q: Qubit):
    print(f"setting LO to {q.xy.lo_conf.freq}")
    q.xy.get_lo().set_frequency(q.xy.lo_conf.freq)


def generate_power_rabi_ef_program(machine: QuAM, batches: BatchJob[Qubit]):
    with program() as prog:
        batches.declare_all()

        for b, q in batches:
            set_lo_freq(batches, q)
            I = b.declare_result_var("fixed", "I")
            Q = b.declare_result_var("fixed", "Q")
            machine.all_flux_to_idle()
            align()
            with b.for_axis("avg", average=True, progress=True):
                with b.for_axis("amp") as amplitude:
                    # q.z.to_idle()
                    q.initialize_thermal(5)
                    update_frequency(q.xy.name(), 200e6)
                    q.xy.play("x")
                    update_frequency(q.xy.name(), 200e6 - q.anharmonicity)

                    q.xy.play("x", amplitude=amplitude)

                    q.rr.measure_iq(I, Q)
                    b.save_all_results()

        with stream_processing():
            batches.do_stream_processing()

    return BatchProgram(prog, machine.generate_config(), batches)

# %% Calibrate
batches = BatchJob([
    Batch(q.name, q, [
        QuaAxis('int', "avg", start=0, stop=params["n_avg"], step=1),
        QuaAxis('fixed', "amp", start=0.0, stop=1.5, step=0.02)
    ]) for q in machine.active_qubits()
])

with TempModifications(machine):
    for q in machine.active_qubits():
        print(f"{q.name} before: lo={q.xy.lo_conf.freq}, if={q.xy.f_if_01}, lo+if={q.xy.lo_conf.freq + q.xy.f_if_01}")
        shift = q.anharmonicity / 2 + 40e6
        q.xy.lo_conf.freq += (q.xy.f_if_01 - shift)
        q.xy.f_if_01 = shift
        print(f"{q.name} after: lo={q.xy.lo_conf.freq}, if={q.xy.f_if_01}, lo+if={q.xy.lo_conf.freq + q.xy.f_if_01}")

    prog = generate_power_rabi_ef_program(machine, batches)
    job = prog.execute(machine)

