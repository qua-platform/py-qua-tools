from qm.octave.calibration_db import CalibrationDB
from typing import Union
from qm.QmJob import QmJob
from qm.jobs.running_qm_job import RunningQmJob
from qm.QuantumMachine import QuantumMachine


def get_calibration_parameters(
    path_to_database: str,
    config: dict,
    element: str,
    LO: float,
    IF: float,
    gain: float,
    verbose_level: int = 2,
) -> dict:
    """Returns the most up-to-date correction parameters in the database, located at the specified path_to_database, for the
    specified values of the Octave LO frequency, intermediate frequency and Octave gain.

    The correction parameters are returned in a dictionary of the form:
    ```{"offsets": {"I": I_offset, "Q": Q_offset}, "correction_matrix": correction}```.

    If the correction parameters are not found in the database:
      * verbose_level=2 will raise a warning which will block the execution.
      * verbose_level=1 will print a warning which will not block the execution  and the returned dictionary will be empty.
      * verbose_level=0 will not print anything and the returned dictionary will be empty.

    :param path_to_database: direct path to the calibration database (without '/calibration_db.json').
    :param config: the OPX config dictionary.
    :param element: the element to get the correction parameters for.
    :param LO: the LO frequency in Hz.
    :param IF: the intermediate frequency in Hz.
    :param gain: the Octave gain.
    :param verbose_level: set the type of messages printed in the Python console. Default is 2.
    :return: dictionary containing the 'I' and 'Q' offsets and the correction_matrix.
    """
    oct_name = config["elements"][element]["RF_inputs"]["port"][0]
    channel = config["elements"][element]["RF_inputs"]["port"][1]
    cal_db = CalibrationDB(path_to_database)
    lo_cal = cal_db.get_lo_cal((oct_name, channel), LO, gain)
    if_cal = cal_db.get_if_cal((oct_name, channel), LO, gain, IF)

    param = {"offsets": {}, "correction_matrix": ()}
    if lo_cal is not None:
        param["offsets"]["I"] = lo_cal.i0
        param["offsets"]["Q"] = lo_cal.q0

        if if_cal is not None:
            param["correction_matrix"] = if_cal.correction
        else:
            if verbose_level == 2:
                raise Warning(
                    f"No correction parameters were found for the provided set of LO frequency, IF and gain.\nIn particular, the IF is missing for the specified LO frequency and gain: LO={LO} Hz, IF={IF} Hz gain={gain}."
                )
            elif verbose_level == 1:
                print(
                    f"No correction parameters were found for the provided set of LO frequency, IF and gain.\nIn particular, the IF is missing for the specified LO frequency and gain: LO={LO} Hz, IF={IF} Hz gain={gain}."
                )
    else:
        if verbose_level == 2:
            raise Warning(
                f"No correction parameters were found for the provided set of LO frequency and gain: LO={LO} Hz, gain={gain}."
            )
        elif verbose_level == 1:
            print(
                f"No correction parameters were found for the provided set of LO frequency and gain: LO={LO} Hz, gain={gain}."
            )

    return param


def set_correction_parameters(
    path_to_database: str,
    config: dict,
    element: str,
    LO: float,
    IF: float,
    gain: float,
    qm: QuantumMachine,
    job: Union[QmJob, RunningQmJob] = None,
    verbose_level: int = 2,
) -> dict:
    """Look for the correction parameters in the database, located at the specified path_to_database, for the specified values of
    the Octave LO frequency, intermediate frequency and Octave gain and update the running job.

    If the correction parameters are not found in the database:
      * verbose_level=2 will raise a warning which will block the execution.
      * verbose_level=1 will print a warning which will not block the execution and correction settings will be unchanged.
      * verbose_level=0 will not print anything and correction settings will be unchanged.
    :param path_to_database: direct path to the calibration database (without '/calibration_db.json').
    :param config: the OPX config dictionary.
    :param element: the element to get the correction parameters for.
    :param LO: the LO frequency in Hz.
    :param IF: the intermediate frequency in Hz.
    :param gain: the Octave gain.
    :param qm: the opened quantum machine.
    :param job: the running job.
    :param verbose_level: set the type of messages printed in the Python console. Default is 2.
    :return: dictionary containing the 'I' and 'Q' offsets and the correction_matrix.
    """
    param = get_calibration_parameters(
        path_to_database, config, element, LO, IF, gain, verbose_level
    )
    if "I" in param["offsets"] and "Q" in param["offsets"]:
        qm.set_output_dc_offset_by_element(
            element, ("I", "Q"), (param["offsets"]["I"], param["offsets"]["Q"])
        )
    if job is None:
        job = qm.get_running_job()
    if len(param["correction_matrix"]) == 4:
        job.set_element_correction(element, param["correction_matrix"])
    return param
