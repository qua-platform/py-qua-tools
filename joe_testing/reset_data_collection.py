# example of how the reset data collection could go

from qualang_tools.analysis import DiscriminatorDataclass
from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager


def run_reset_program(qua_reset_program, host, port):
    # connect and open QM
    qmm = QuantumMachinesManager(host=host, port=port)
    qm = qmm.open_qm()




