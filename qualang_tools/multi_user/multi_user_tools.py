import logging
from contextlib import contextmanager
from time import sleep, time
from typing import Generator

from qm import QuantumMachinesManager, QuantumMachine, QopCaps
from qm.logging_utils import set_logging_level

msg = "cannot be used because it isn't shareable in other QM."
msg_opx1000 = "Resources already locked"


@contextmanager
def qm_session(qmm: QuantumMachinesManager, config: dict, timeout: int = 100) -> Generator[QuantumMachine, None, None]:
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
        raise ValueError(f"{timeout=} must be positive")

    qm_log = logging.getLogger("qm.api.frontend_api")  # formerly "qm" & qm.api.frontend_api
    is_busy = True
    printed = False
    t0 = time()
    elapsed_time = 0
    while is_busy and elapsed_time < timeout:
        try:
            qm = qmm.open_qm(config, close_other_machines=False)

        except Exception as e:
            if (qmm.capabilities.supports(QopCaps.qop3) and msg_opx1000 in str(e)) or (
                ~qmm.capabilities.supports(QopCaps.qop3) and msg in str(e)
            ):
                if not printed:
                    qm_log.error(f"QOP is busy. Waiting for it to free up for {timeout}s...")
                    set_logging_level("CRITICAL")

                    printed = True
                sleep(0.2)
                elapsed_time = time() - t0
            else:
                raise Exception from e
        else:
            is_busy = False
            set_logging_level("INFO")
            qm_log.info("Opening QM")

    if is_busy and elapsed_time >= timeout:
        qm_log.warning(f"While waiting for QOP to free, reached timeout: {timeout}s")
        raise TimeoutError(f"While waiting for QOP to free, reached timeout: {timeout}s")
    try:
        yield qm

        if qmm.capabilities.supports(QopCaps.qop3):
            while qm.get_jobs(status=["Running"]):
                sleep(0.2)
        else:
            while qm.get_running_job() is not None:
                sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        qm_log.info("Closing QM")
        qm.close()
