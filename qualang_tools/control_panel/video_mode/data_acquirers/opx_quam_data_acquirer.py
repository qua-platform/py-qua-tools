from typing import Any, Callable, Literal, Optional

from qm import QuantumMachinesManager

from qualang_tools.control_panel.video_mode.data_acquirers.opx_data_acquirer import OPXDataAcquirer
from qualang_tools.control_panel.video_mode.scan_modes import ScanMode
from qualang_tools.control_panel.video_mode.sweep_axis import SweepAxis


__all__ = ["OPXQuamDataAcquirer"]


class OPXQuamDataAcquirer(OPXDataAcquirer):
    """Data acquirer for OPX devices using QUAM.

    This class is responsible for acquiring data from OPX devices using QUAM.

    Args:
        qmm: The QuantumMachinesManager instance.
        machine: The QUAM machine instance to use.
        qua_inner_loop_action: The inner loop action to execute.
        scan_mode: The scan mode to use.
        x_axis: The x-axis of the data acquirer.
        y_axis: The y-axis of the data acquirer.
        num_averages: The number of averages to take as a rolling average.
        result_type: The type of result to acquire.
        initial_delay: The initial delay before starting each scan.
    """

    def __init__(
        self,
        *,
        qmm: QuantumMachinesManager,
        machine: Any,
        qua_inner_loop_action: Callable,
        scan_mode: ScanMode,
        x_axis: SweepAxis,
        y_axis: SweepAxis,
        num_averages=1,
        result_type: Literal["I", "Q", "amplitude", "phase"] = "I",
        initial_delay: Optional[float] = None,
        **kwargs,
    ):
        self.machine = machine
        qua_config = machine.generate_config()

        super().__init__(
            qmm=qmm,
            qua_config=qua_config,
            qua_inner_loop_action=qua_inner_loop_action,
            scan_mode=scan_mode,
            x_axis=x_axis,
            y_axis=y_axis,
            num_averages=num_averages,
            result_type=result_type,
            initial_delay=initial_delay,
            **kwargs,
        )

    def generate_config(self):
        self.qua_config = self.machine.generate_config()
        self.qm = self.qmm.open_qm(self.qua_config)
