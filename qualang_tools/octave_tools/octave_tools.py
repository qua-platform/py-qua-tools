import numpy as np
from qm.octave.calibration_db import CalibrationDB
from typing import Union
from qm import QmJob
from qm.jobs.running_qm_job import RunningQmJob
from qm import QuantumMachine
from qm.octave.octave_mixer_calibration import AutoCalibrationParams


def get_calibration_parameters_from_db(
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


def set_correction_parameters_to_opx(
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
    """Look for the correction parameters in the database, located at path_to_database, for the specified values of
    the Octave LO frequency, intermediate frequency and Octave gain and update the running job with `job.set_element_correction()`.
    If no job is specified, then the running will be taken using `qm.get_running_job()`.
    If no job is running, then the loaded mixer correction matrix is updated using `qm.set_mixer_correction()`.
    The correction parameters are returned in a dictionary of the form:
    ```{"offsets": {"I": I_offset, "Q": Q_offset}, "correction_matrix": correction}```.

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
    :param job: the running job. If None, then the running will be taken using `qm.get_running_job()`.
    :param verbose_level: set the type of messages printed in the Python console. Default is 2.
    :return: dictionary containing the 'I' and 'Q' offsets and the correction_matrix.
    """
    param = get_calibration_parameters_from_db(path_to_database, config, element, LO, IF, gain, verbose_level)
    if "I" in param["offsets"] and "Q" in param["offsets"]:
        qm.set_output_dc_offset_by_element(element, ("I", "Q"), (param["offsets"]["I"], param["offsets"]["Q"]))
    if job is None:
        job = qm.get_running_job()
        if job is not None:
            job.set_element_correction(element, param["correction_matrix"])
        else:
            mixer_name = qm.get_config()["elements"][element]["mixInputs"]["mixer"]
            lo_conf = qm.get_config()["elements"]["q0.resonator"]["mixInputs"]["lo_frequency"]
            if_conf = qm.get_config()["elements"]["q0.resonator"]["intermediate_frequency"]
            if IF != if_conf:
                print(
                    "WARNING: the intermediate frequency doesn't match the one defined in the config, which means that the loaded correction matrix may not be optimal."
                )
            qm.set_mixer_correction(mixer_name, if_conf, lo_conf, tuple(param["correction_matrix"]))
    return param


def get_correction_for_each_LO_and_IF(
    path_to_database: str,
    config: dict,
    element: str,
    gain: float,
    LO_list: Union[list, np.ndarray],
    IF_list: Union[list, np.ndarray],
    nb_of_updates: int,
    calibrate: bool = False,
    qm: QuantumMachine = None,
    calibration_params: AutoCalibrationParams = None,
):
    """Look in the calibration database for the calibration parameters corresponding to the provided set of LO
    frequencies, intermediate frequencies and gain.
    The intermediate frequencies considered here are only the ```nb_of_updates``` equally spaced frequencies from the
    provided ```IF_list```. For instance, if a list of 100 intermediate frequencies is provided, but nb_of_update is set
    to 10, then only 10 correction parameters will be returned for the returned equally spaced intermediate frequencies.

    The goal is to perform a wide frequency sweep (scan the LO frequency in Python and the IF in QUA) and update the
    mixer correction parameters for each LO frequency and a few intermediate frequencies, given by ```nb_of_updates```,
    in QUA.

    If the flag ```calibrate``` is set to True (the opened Quantum Machine needs to be provided), then the specified element will be calibrated at the given frequencies
    (all LO frequencies and only the ``nb_of_updates``` intermediate frequencies).
    Custom calibration parameters can be passed using the `calibration_params` dataclass. For instance:
    ```calibration_params = AutoCalibrationParams(); calibration_params.if_amplitude = 0.25```

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
    :param calibration_params: class containing the calibration parameters (if_amplitude, offset_frequency...). Default is None.
    :return: the list on intermediate frequencies at which the correction matrix will be updated in the
    program (size nb_of_updates), the 'I' and 'Q' offsets and the four coefficients of the correction matrix with one element for each pair
    (LO, IF) (size nb_of_updates*len(LO_list)): IFs, c00, c01, c10, c11, offset_I, offset_Q.
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
            qm.calibrate_element(element, {lo: tuple(IFs)}, params=calibration_params)
        elif calibrate and qm is None:
            raise Exception(
                "The opened Quantum Machine object must be provided if the flag ```calibrate``` is set to True."
            )

        for i in IFs:
            param = get_calibration_parameters_from_db(path_to_database, config, element, lo, i, gain)
            c00.append(param["correction_matrix"][0])
            c01.append(param["correction_matrix"][1])
            c10.append(param["correction_matrix"][2])
            c11.append(param["correction_matrix"][3])
            if i == IFs[0]:
                offset_I.append(param["offsets"]["I"])
                offset_Q.append(param["offsets"]["Q"])
    return IFs, c00, c01, c10, c11, offset_I, offset_Q


def octave_calibration_tool(
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
