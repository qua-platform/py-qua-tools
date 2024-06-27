import logging
from contextlib import contextmanager
from time import sleep

from qm import QuantumMachine
from qm import QuantumMachinesManager

msg = (
    "A quantum machine cannot be opened because an existing quantum machine, using the same ports, is currently "
    "running a program. Please close the currently open quantum machine."
)


class BusyFilter(logging.Filter):
    def filter(self, record):
        return not ("already uses" in record.getMessage() or msg in record.getMessage())


@contextmanager
def qm_session(qmm: QuantumMachinesManager, config: dict, timeout: int = 100) -> QuantumMachine:
    """
    This context manager allows a user to _try_ to
    open a quantum machine, and if it is not possible since its resources are currently in use,
    wait for them to free up. This is done by repeatedly polling the QM manager.

    Once they are freed, execution will start automatically.
    Once the context manager code block is exited, the QM will close automatically, freeing it up
    for another user.

    :param qmm: A QM manager from which to open QM
    :param config: a QUA config that will be supplied to `open_qm`
    :param timeout: time in seconds to wait for resources to free up before raising exception

    """
    if not timeout > 0:
        raise ValueError(f"timeout={timeout} but must be positive")
    qm_log = logging.getLogger("qm")
    filt = BusyFilter()
    is_busy = True
    printed = False
    time = 0
    while is_busy and time < timeout:
        try:
            qm_log.addFilter(filt)
            qm = qmm.open_qm(config, close_other_machines=False)
            # qm_log.warning(f"QOP is busy. Waiting for it to free up for {timeout}s...")
        except Exception as e:
            if (
                hasattr(e, "errors")
                and isinstance(e.errors, list)
                and len(e.errors) > 1
                and isinstance(e.errors[1], tuple)
                and len(e.errors[1]) > 2
                and msg in e.errors[1][2]
            ):
                if not printed:
                    qm_log.warning(f"QOP is busy. Waiting for it to free up for {timeout}s...")
                    printed = True
                sleep(0.2)
                time += 0.2
            else:
                raise Exception from e
        else:
            is_busy = False
            qm_log.info("Opening QM")
        finally:
            qm_log.removeFilter(filt)
    if is_busy and time >= timeout:
        qm_log.warning(f"While waiting for QOP to free, reached timeout: {timeout}s")
        raise TimeoutError(f"While waiting for QOP to free, reached timeout: {timeout}s")
    try:
        yield qm
        while qm.get_running_job() is not None:
            sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        qm_log.info("Closing QM")
        qm.close()
