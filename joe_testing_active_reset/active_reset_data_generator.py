#%%
from platform import mac_ver
from quam import QuAM
from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.simulate import SimulationConfig
from qualang_tools.loops import from_array
from qualang_tools.results import fetching_tool, progress_counter
from qualang_tools.analysis.discriminator import two_state_discriminator

import matplotlib.pyplot as plt

import numpy as np
# from IPython.display import clear_output


# %%
n_shots = int(2000)
num_qb = 6

n_total = num_qb * n_shots
cooldown_time = int(0.6e-3 / 4e-9)

def construct_active_reset_program():

    with program() as active_reset_program:
        raw_st = declare_stream(adc_trace=True)
        n = declare(int)
        n_cnt = declare(int, value=0)
        #     threshold = declare(fixed)

        I = [declare(fixed) for idx in range(num_qb)]
        I_herald = [declare(fixed) for idx in range(num_qb)]
        Q = [declare(fixed) for idx in range(num_qb)]
        I_st = [declare_stream() for idx in range(num_qb)]
        Q_st = [declare_stream() for idx in range(num_qb)]
        N_st = declare_stream()

        threshold = []
        for idx in range(num_qb):
            threshold.append(machine.readout_resonators[idx].threshold)

        with for_(n, 0, n < n_shots, n + 1):
            for idx in range(num_qb):
                #             update_frequency(f"qb{idx}", 0)
                #             reset_phase(f"qb{idx}")

                play("x90", f"qb{idx}")
                #             play("x180", f"qb{idx}")

                wait(int(200e-9 // 4e-9), f"qb{idx}")

                align(f"qb{idx}", f"rr{idx}")

                measure("readout", f"rr{idx}", None,
                        dual_demod.full("rotated_cos", "out1", "rotated_minus_sin", "out2", I_herald[idx]))
                align(f"qb{idx}", f"rr{idx}")

                wait(int(4e-6 // 4e-9), f"qb{idx}")

                with if_(I_herald[idx] < threshold[idx]):
                    # pi
                    play("x180", f"qb{idx}")

                align(f"qb{idx}", f"rr{idx}")

                measure("readout", f"rr{idx}", None,
                        dual_demod.full("rotated_cos", "out1", "rotated_minus_sin", "out2", I[idx]),
                        dual_demod.full("rotated_sin", "out1", "rotated_cos", "out2", Q[idx]))

                wait(cooldown_time, f"rr{idx}")
                #             wait(int(1e-6//4e-9), f"rr{idx}")

                save(I[idx], I_st[idx])
                save(Q[idx], Q_st[idx])
                assign(n_cnt, n_cnt + 1)
            save(n_cnt, N_st)

        with stream_processing():
            N_st.save("N")

            for idx in range(num_qb):
                I_st[idx].save_all(f'I{idx}')
                Q_st[idx].save_all(f'Q{idx}')

    return active_reset_program