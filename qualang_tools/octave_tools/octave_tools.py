from qm.octave.calibration_db import CalibrationDB
from typing import Union
from qm.QmJob import QmJob
from qm.jobs.running_qm_job import RunningQmJob
from qm.QuantumMachine import QuantumMachine


def get_calibration_parameters(
    path: str, config: dict, element: str, LO: float, IF: float, gain: float
) -> dict:
    """Look for the correction parameters in the database, located at the specified path, for the specified values of
    the Octave frequency, intermediate frequency and Octave gain.

    The correction parameters are returned in a dictionary of the form:
    ```{"offsets": {"I": I_offset, "Q": Q_offset}, "correction_matrix": correction}```.

    If no parameters are found for the specified values, the returned dictionary will be empty.

    :param path: direct path to the calibration database (without '/calibration_db.json').
    :param config: the OPX config dictionary.
    :param element: the element to get the correction parameters for.
    :param LO: the LO frequency in Hz.
    :param IF: the intermediate frequency in Hz.
    :param gain: the Octave gain.
    :return: dictionary containing the 'I' and 'Q' offsets and the correction_matrix.
    """
    oct_name = config["elements"][element]["RF_inputs"]["port"][0]
    channel = config["elements"][element]["RF_inputs"]["port"][1]
    cal_db = CalibrationDB(path)
    lo_cal = cal_db.get_lo_cal((oct_name, channel), LO, gain)
    if_cal = cal_db.get_if_cal((oct_name, channel), LO, gain, IF)
    param = {"offsets": {}, "correction_matrix": ()}
    if lo_cal is not None:
        param["offsets"]["I"] = lo_cal.i0
        param["offsets"]["Q"] = lo_cal.q0
    else:
        raise Warning(
            "No correction parameters were found for the provided set of LO frequency and gain"
        )
    if if_cal is not None:
        param["correction_matrix"] = if_cal.correction
    else:
        raise Warning(
            "No correction parameters were found for the provided set of LO frequency, IF and gain"
        )
    return param


def set_correction_parameters(
    path: str,
    config: dict,
    element: str,
    LO: float,
    IF: float,
    gain: float,
    qm: QuantumMachine,
    job: Union[QmJob, RunningQmJob] = None,
) -> None:
    """Look for the correction parameters in the database, located at the specified path, for the specified values of
    the Octave frequency, intermediate frequency and Octave gain and update the running job.

    :param path: direct path to the calibration database (without '/calibration_db.json').
    :param config: the OPX config dictionary.
    :param element: the element to get the correction parameters for.
    :param LO: the LO frequency in Hz.
    :param IF: the intermediate frequency in Hz.
    :param gain: the Octave gain.
    :param qm: the opened quantum machine.
    :param job: the running job.
    """
    param = get_calibration_parameters(path, config, element, LO, IF, gain)
    qm.set_output_dc_offset_by_element(
        element, ("I", "Q"), (param["offsets"]["I"], param["offsets"]["Q"])
    )
    if job is None:
        job = qm.get_running_job()
    job.set_element_correction(element, param["correction_matrix"])
