import numpy as np
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
    param = get_calibration_parameters(path_to_database, config, element, LO, IF, gain, verbose_level)
    if "I" in param["offsets"] and "Q" in param["offsets"]:
        qm.set_output_dc_offset_by_element(element, ("I", "Q"), (param["offsets"]["I"], param["offsets"]["Q"]))
    if job is None:
        job = qm.get_running_job()
    if len(param["correction_matrix"]) == 4:
        job.set_element_correction(element, param["correction_matrix"])
    return param


def update_correction_for_each_IF(
    path_to_database: str,
    config: dict,
    element: str,
    gain: float,
    LO_list: Union[list, np.ndarray],
    IF_list: Union[list, np.ndarray],
    nb_of_updates: int,
    calibrate: bool = False,
    qm: QuantumMachine = None,
):
    """Look in the calibration database for the calibration parameters corresponding to the provided set of LO
    frequencies, intermediate frequencies and gain.
    The intermediate frequencies considered here are only the ```nb_of_updates``` equally spaced frequencies from the
    provided ```IF_list```.

    The goal is to perform a wide frequency sweep (scan the LO frequency in Python and the IF in QUA) and update the
    mixer correction parameters for each LO frequency and a few intermediate frequencies, given by ```nb_of_updates```,
    in QUA.

    If the flag ```calibrate``` is set to True (the opened Quantum Machine needs to be provided), then the specified element will be calibrated at the given frequencies
    (all LO frequencies and only the ``nb_of_updates``` intermediate frequencies).

    The function will return the list on intermediate frequencies at which the correction matrix will be updated in the
    program, the 'I' and 'Q' offsets and the four coefficients of the correction matrix with one element for each pair (LO, IF).

    :param path_to_database: direct path to the calibration database (without '/calibration_db.json').
    :param config: the OPX config dictionary.
    :param element: the element to get the correction parameters for.
    :param gain: the Octave gain.
    :param LO_list: list of the LO frequencies involved in the scan, in Hz.
    :param IF_list: list of the intermediate frequencies involved in the scan, in Hz.
    :param nb_of_updates: number of intermediate frequencies to calibrate and for which the program will update the correction pmatrix.
    :param calibrate: calibrate all the frequencies involved to the scan (LO and IF for the specified gain). Default is False.
    :param qm: the quantum machine object. Default is None.
    :return: the list on intermediate frequencies at which the correction matrix will be updated in the
    program, the 'I' and 'Q' offsets and the four coefficients of the correction matrix with one element for each pair
    (LO, IF): IFs, c00, c01, c10, c11, offset_I, offset_Q.
    """
    N = len(IF_list)
    IFs = [IF_list[i * N // nb_of_updates] for i in range(nb_of_updates)]
    c00 = []
    c01 = []
    c10 = []
    c11 = []
    offset_I = []
    offset_Q = []

    for lo in LO_list:
        if calibrate and qm is not None:
            qm.calibrate_element(element, {lo: tuple(IFs)})
        elif qm is None:
            raise Exception(
                "The opened Quantum Machine object must be provided if the flag ```calibrate``` is set to True."
            )

        for i in IFs:
            param = get_calibration_parameters(path_to_database, config, element, lo, i, gain)
            c00.append(param["correction_matrix"][0])
            c01.append(param["correction_matrix"][1])
            c10.append(param["correction_matrix"][2])
            c11.append(param["correction_matrix"][3])
            if i == IFs[0]:
                offset_I.append(param["offsets"]["I"])
                offset_Q.append(param["offsets"]["Q"])
    return IFs, c00, c01, c10, c11, offset_I, offset_Q


def octave_calibration(
    qm: QuantumMachine,
    element: str,
    lo_frequencies: Union[int, float, list, np.ndarray],
    intermediate_frequencies: Union[int, float, list, np.ndarray],
):
    """Calibrate a given element for a list of LO and intermediate frequencies.
    :param qm: the quantum machine object.
    :param element: the element to calibrate.
    :param lo_frequencies: single value or list of LO frequencies to calibrate in Hz.
    :param intermediate_frequencies: single value or list of Intermediate frequencies to calibrate in Hz.
    """
    if not isinstance(lo_frequencies, Union[list, np.ndarray]):
        lo_frequencies = [lo_frequencies]

    if not isinstance(intermediate_frequencies, Union[list, np.ndarray]):
        intermediate_frequencies = [intermediate_frequencies]

    for lo in lo_frequencies:
        qm.calibrate_element(element, {lo: tuple(intermediate_frequencies)})
