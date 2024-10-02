import sys
import threading
from typing import Any

from PyQt5.QtWidgets import QApplication

from qualang_tools.control_panel.voltage_control.voltage_control_dialog import VoltageControlDialog


def start_voltage_control(use_thread: bool = False, gui_name: str = "Voltage control", *args: Any, **kwargs: Any):
    """
    Start the voltage control GUI.

    Args:
        use_thread: Whether to run the GUI in a separate thread
        gui_name: Name of the GUI thread
        *args: Positional arguments to pass to VoltageControlDialog
        **kwargs: Keyword arguments to pass to VoltageControlDialog

    Returns:
        QApplication instance or threading.Thread instance
    """
    if use_thread:
        if any(t.name == gui_name for t in threading.enumerate()):
            raise RuntimeError(f"GUI {gui_name} already exists. Exiting")
        t = threading.Thread(
            target=start_voltage_control,
            name=gui_name,
            args=args,
            kwargs={"use_thread": False, "gui_name": gui_name, **kwargs},
        )
        t.start()
        return t
    else:
        qApp = QApplication(sys.argv)

        aw = VoltageControlDialog(*args, **kwargs)
        aw.show()
        qApp.exec_()
        return qApp


if __name__ == "__main__":
    from qcodes.parameters import ManualParameter
    import numpy as np

    # Create dummy parameters
    parameters = [ManualParameter(f"V{idx}", initial_value=np.round(np.random.rand(), 3)) for idx in range(15)]
    start_voltage_control(parameters=parameters, mini=True, use_thread=False)
