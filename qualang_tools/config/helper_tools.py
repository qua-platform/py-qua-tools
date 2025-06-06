from collections import UserDict as _UserDict
from copy import deepcopy as _deepcopy
from typing import List, Tuple
import json as _json
from pprint import pprint
import numpy as np
from qualang_tools.units import unit
from qualang_tools.config.intrument_limits import (
    OCTAVE_GAIN_MAX,
    OCTAVE_GAIN_MIN,
    OCTAVE_GAIN_STEP,
    OPX_AMPLITUDE_MIN,
    OPX_AMPLITUDE_MAX,
    OPX1000_MW_POWER_STEP,
    OPX1000_MW_POWER_MIN,
    OPX1000_MW_POWER_MAX,
    OPX1000_MW_AMPLITUDE_MIN,
    OPX1000_MW_BANDS,
)


def get_band(freq):
    """Determine the MW fem DAC band corresponding to a given frequency.

    Args:
        freq (float): The frequency in Hz.

    Returns:
        int: The Nyquist band number.

    Raises:
        ValueError: If the frequency is outside the MW fem bandwidth.
    """
    possible_bands = []
    distance_from_edge = []
    for band in OPX1000_MW_BANDS:
        if OPX1000_MW_BANDS[band][0] <= freq <= OPX1000_MW_BANDS[band][1]:
            possible_bands.append(band)
            distance_from_edge.append(min(freq - OPX1000_MW_BANDS[band][0], OPX1000_MW_BANDS[band][1] - freq))
    if len(possible_bands) > 0:
        return possible_bands[np.argmax(distance_from_edge)]
    else:
        raise ValueError(
            f"The specified frequency {freq} Hz is outside of the MW fem bandwidth [{min(min(OPX1000_MW_BANDS.values())) * 1e-6} MHz, {max(max(OPX1000_MW_BANDS.values())) * 1e-9} GHz]"
        )


def _closest_number(lst, target):
    return min(lst, key=lambda x: abs(x - target))


def get_full_scale_power_dBm_and_amplitude(desired_power: float, max_amplitude: float = 0.5) -> tuple[int, float]:
    """Get the full_scale_power_dbm and waveform amplitude for the MW FEM to output the specified desired power.

    The keyword `full_scale_power_dbm` is the maximum power of normalized pulse waveforms in [-1,1].
    To convert to voltage:
        power_mw = 10**(full_scale_power_dbm / 10)
        max_voltage_amp = np.sqrt(2 * power_mw * 50 / 1000)
        amp_in_volts = waveform * max_voltage_amp
        ^ equivalent to OPX+ amp
    Its range is -11dBm to +16dBm with 3dBm steps.

    Args:
        desired_power (float): Desired output power in dBm.
        max_amplitude (float, optional): Maximum allowed waveform amplitude in V. Default is 0.5V.

    Returns:
        tuple[float, float]: The full_scale_power_dBm and waveform amplitude realizing the desired power.
    """
    allowed_power = np.arange(
        OPX1000_MW_POWER_MIN, OPX1000_MW_POWER_MAX + OPX1000_MW_POWER_STEP / 2, OPX1000_MW_POWER_STEP, dtype=int
    ).tolist()

    resulting_power = desired_power - 20 * np.log10(max_amplitude)
    if resulting_power < 0:
        full_scale_power_dBm = _closest_number(
            allowed_power, max(resulting_power + OPX1000_MW_POWER_STEP, OPX1000_MW_POWER_MIN)
        )
    else:
        full_scale_power_dBm = _closest_number(
            allowed_power, min(resulting_power + OPX1000_MW_POWER_STEP, OPX1000_MW_POWER_MAX)
        )
    amplitude = 10 ** ((desired_power - full_scale_power_dBm) / 20)
    if (
        OPX1000_MW_POWER_MIN <= full_scale_power_dBm <= OPX1000_MW_POWER_MAX
        and -max_amplitude <= amplitude <= max_amplitude
    ):
        return full_scale_power_dBm, amplitude
    else:
        raise ValueError(
            f"The desired power is outside the specifications ([{OPX1000_MW_POWER_MIN}; +{OPX1000_MW_POWER_MAX}]dBm, [{OPX1000_MW_AMPLITUDE_MIN}; +{OPX1000_MW_AMPLITUDE_MIN}]), got ({full_scale_power_dBm}; {amplitude})"
        )


def get_octave_gain_and_amplitude(desired_power: float, max_amplitude: float = 0.125) -> tuple[float, float]:
    """Get the Octave gain and IF amplitude for the Octave to output the specified desired power.

    Args:
        desired_power (float): Desired output power in dBm.
        max_amplitude (float, optional): Maximum allowed IF amplitude provided by the OPX to the Octave in V. Default is 0.125V, which is the optimum for driving the Octave up-conversion mixers.

    Returns:
        tuple[float, float]: The Octave gain and IF amplitude realizing the desired power.
    """
    u = unit(coerce_to_integer=True)

    resulting_power = desired_power - u.volts2dBm(max_amplitude)
    if resulting_power < 0:
        octave_gain = round(max(desired_power - u.volts2dBm(max_amplitude) + OCTAVE_GAIN_STEP, OCTAVE_GAIN_MIN) * 2) / 2
    else:
        octave_gain = round(min(desired_power - u.volts2dBm(max_amplitude) + OCTAVE_GAIN_STEP, OCTAVE_GAIN_MAX) * 2) / 2
    amplitude = u.dBm2volts(desired_power - octave_gain)

    if OCTAVE_GAIN_MIN <= octave_gain <= OCTAVE_GAIN_MAX and -max_amplitude <= amplitude < max_amplitude:
        return octave_gain, amplitude
    else:
        raise ValueError(
            f"The desired power is outside the specifications ([{OCTAVE_GAIN_MIN}; +{OCTAVE_GAIN_MAX}]dBm, [{OPX_AMPLITUDE_MIN}; +{OPX_AMPLITUDE_MAX})V), got ({octave_gain}; {amplitude})"
        )


def transform_negative_delays(config, create_new_config=False):
    """
    Adds the most negative delay to all the elements in the configuration.

    :param config: A valid QOP configuration.
    :param create_new_config: If true, returns a new copy of the configuration.
        If false, edits the existing configuration. Default is false.
    :returns: The edited configuration.
    """
    min_delay = 0
    if create_new_config:
        config = _deepcopy(config)
    cons = config.get("controllers")
    for con in cons:
        ports = cons.get(con).get("analog_outputs")
        for port in ports:
            min_delay = min(ports.get(port).get("delay", 0), min_delay)

    if min_delay < 0:
        for con in cons:
            ports = cons.get(con).get("analog_outputs")
            for port in ports:
                delay = ports.get(port).get("delay", 0)
                ports.get(port)["delay"] = delay - min_delay
    return config


class QuaConfig(_UserDict):
    def __init__(self, data):
        super().__init__(data)
        self._data_orig = _deepcopy(data)
        self.pulse_suffix = "_pulse"
        self.wf_suffix = "_wf"

    def print(self):
        """
        Print the config using pprint.
        """
        return pprint(self)

    def reset(self):
        """
        Reset to config to its initial state.
        """
        self.data = _deepcopy(self._data_orig)

    def dump(self, filename):
        with open(filename, "w") as fp:
            _json.dump(self.data, fp)

    def add_control_operation_iq(self, element: str, operation_name: str, wf_i: List[float], wf_q: List[float]):
        """
        Add or update a control operation to a mixed input element.

        :param element: name of the mixed input element to add the operation to. Must be defined in the configuration.
        :param operation_name: name of the operation to be added.
        :param wf_i: list of points defining the waveform for the 'I' quadrature. Must have the same length as wf_q.
        :param wf_q: list of points defining the waveform for the 'Q' quadrature. Must have the same length as wf_i.
        """

        # Check inputs
        if element not in self.data["elements"].keys():
            raise KeyError(f"The element '{element}' in not defined in the config.")
        if "mixInputs" not in self.data["elements"][element].keys():
            raise KeyError(f"Element '{element}' is not a mixInputs element.")
        if len(wf_i) != len(wf_q):
            raise ValueError("The 'I' and 'Q' waveforms must have the same length.")

        # Add operation
        pulse_name = element + "_" + operation_name + self.pulse_suffix
        wf_name = element + "_" + operation_name + self.wf_suffix
        self.data["elements"][element]["operations"][operation_name] = pulse_name
        # Add pulse
        self.data["pulses"][pulse_name] = {
            "operation": "control",
            "length": len(wf_i),
            "waveforms": {"I": wf_name + "_i", "Q": wf_name + "_q"},
        }
        # Add waveform
        self.update_waveforms(element, operation_name, (wf_i, wf_q))

    def add_control_operation_single(self, element: str, operation_name: str, wf: List[float]):
        """
        Add or update a control operation to a single input element.

        :param element: name of the single input element to add the operation to. Must be defined in the configuration.
        :param operation_name: name of the operation to be added.
        :param wf: list of points defining the waveform with a 1ns resolution.
        """

        # Check inputs
        if element not in self.data["elements"].keys():
            raise KeyError(f"The element '{element}' in not defined in the config.")
        if "singleInput" not in self.data["elements"][element].keys():
            raise KeyError(f"Element '{element}' is not a singleInput element.")

        # Add operation
        pulse_name = element + "_" + operation_name + self.pulse_suffix
        wf_name = element + "_" + operation_name + "_single" + self.wf_suffix
        self.data["elements"][element]["operations"][operation_name] = pulse_name
        # Add pulse
        self.data["pulses"][pulse_name] = {
            "operation": "control",
            "length": len(wf),
            "waveforms": {"single": wf_name},
        }
        # Add waveform
        self.update_waveforms(element, operation_name, (wf,))

    def get_waveforms_from_op(self, element: str, operation_name: str) -> List or List[List]:
        """
        Get the waveforms corresponding to the given element and operation.

        :param element: name of the element to get the waveforms from. Must be defined in the config.
        :param operation_name: name of the operation to get the waveforms from. Must be defined in the config.
        :return: list of the corresponding waveforms.
        """

        # Check inputs
        if element not in self.data["elements"].keys():
            raise KeyError(f"The element '{element}' in not defined in the config.")
        if operation_name not in self.data["elements"][element]["operations"].keys():
            raise KeyError(
                f"The operation '{operation_name}' in not defined in the config for the element '{element}'."
            )

        # Get the waveforms
        pulse = self.get_pulse_from_op(element, operation_name)
        if "mixInputs" in self.data["elements"][element]:
            waveform_i = self.data["waveforms"][pulse["waveforms"]["I"]]
            if waveform_i["type"] == "arbitrary":
                waveform_i = waveform_i["samples"]
            else:
                waveform_i = [waveform_i["sample"]] * pulse["length"]

            waveform_q = self.data["waveforms"][pulse["waveforms"]["Q"]]
            if waveform_q["type"] == "arbitrary":
                waveform_q = waveform_q["samples"]
            else:
                waveform_q = [waveform_q["sample"]] * pulse["length"]
            return waveform_i, waveform_q
        else:
            waveform = self.data["waveforms"][pulse["waveforms"]["single"]]
            if waveform["type"] == "arbitrary":
                waveform = waveform["samples"]
            else:
                waveform = [waveform["sample"]] * pulse["length"]
            return waveform

    def get_pulse_from_op(self, element: str, operation_name: str) -> dict:
        """
        Get the pulse corresponding to the given element and operation.

        :param element: name of the element to get the waveforms from. Must be defined in the config.
        :param operation_name: name of the operation to get the waveforms from. Must be defined in the config.
        :return: the corresponding pulse as a dictionary.
        """

        # Check inputs
        if element not in self.data["elements"].keys():
            raise KeyError(f"The element '{element}' in not defined in the config.")
        if operation_name not in self.data["elements"][element]["operations"].keys():
            raise KeyError(
                f"The operation '{operation_name}' in not defined in the config for the element '{element}'."
            )

        return self.data["pulses"][self.data["elements"][element]["operations"][operation_name]]

    def update_op_amp(self, element: str, operation_name: str, amp: float, force_update: bool = False):
        """
        Update the operation amplitude.
        Can only access amplitude for a constant pulse of a single element.
        Updating the waveform may affect other elements if it is used in other operations.
        Set the force_update flag to True to update the waveform anyway.

        :param element: name of the element to get the waveforms from. Must be defined in the config.
        :param operation_name: name of the operation to get the waveforms from. Must be defined in the config.
        :param amp: float for the updated amplitude. Must be within the range [-0.5, 0.5) V.
        :param force_update: If True, the waveform will be updated even if it used in other operations.
        """

        # Check inputs
        if element not in self.data["elements"].keys():
            raise KeyError(f"The element '{element}' in not defined in the config.")
        if operation_name not in self.data["elements"][element]["operations"].keys():
            raise KeyError(
                f"The operation '{operation_name}' in not defined in the config for the element '{element}'."
            )
        if not -0.5 <= amp < 0.5:
            raise ValueError("The amplitude must be within the range [-0.5, 0.5) Volts.")
        pulse = self.get_pulse_from_op(element, operation_name)
        if "single" not in pulse["waveforms"].keys():
            raise KeyError("Can only access amplitude for a constant pulse of a single element")
        wf = pulse["waveforms"]["single"]
        # Check if the waveform is used in another pulse
        count = 0
        for key in self.data["pulses"].keys():
            if "single" in self.data["pulses"][key]["waveforms"]:
                if wf == self.data["pulses"][key]["waveforms"]["single"]:
                    count += 1
            elif "I" in self.data["pulses"][key]["waveforms"]:
                if wf == self.data["pulses"][key]["waveforms"]["I"]:
                    count += 1
            elif "Q" in self.data["pulses"][key]["waveforms"]:
                if wf == self.data["pulses"][key]["waveforms"]["Q"]:
                    count += 1
        if count > 1 and not force_update:
            raise Exception(
                "The updated waveform is used in other operations. To force the update, please set the force_update flag to True."
            )
        elif count == 0:
            raise Exception(f"The operation {operation_name} doesn't have a valid waveform.")
        # Update the waveform
        self.data["waveforms"][wf]["sample"] = amp

    def get_op_amp(self, element: str, operation_name: str) -> float:
        """
        Get the amplitude corresponding to the given element and constant operation.
        Can only access amplitude for a constant pulse of a single element.

        :param element: name of the element to get the waveforms from. Must be defined in the config.
        :param operation_name: name of the operation to get the waveforms from. Must be defined in the config.
        :return: the corresponding amplitude.
        """
        # Check inputs
        if element not in self.data["elements"].keys():
            raise KeyError(f"The element '{element}' in not defined in the config.")
        if operation_name not in self.data["elements"][element]["operations"].keys():
            raise KeyError(
                f"The operation '{operation_name}' in not defined in the config for the element '{element}'."
            )

        pulse = self.get_pulse_from_op(element, operation_name)
        try:
            return self.data["waveforms"][pulse["waveforms"]["single"]]["sample"]
        except KeyError:
            raise KeyError("Can only access amplitude for a constant pulse of a single element")

    def update_integration_weight(
        self,
        element: str,
        operation_name: str,
        iw_op_name: str,
        iw_cos: List,
        iw_sin: List,
        force_update: bool = False,
    ):
        """
        Update the cosine and sine parts of an integration weight for a given element and operation.

        :param element: name of the element to get the waveforms from. Must be defined in the config.
        :param operation_name: name of the operation to get the waveforms from. Must be defined in the config.
        :param iw_op_name: name of the integration weight to be updated. Must be defined in the config.
        :param iw_cos: values for the cosine part of integration weights defined as a list of tuples [(value, duration in ns)].
        :param iw_sin: values for the sine part of integration weights defined as a list of tuples [(value, duration in ns)].
        :param force_update: If True, the waveform will be updated even if it used in other operations.
        """
        # Check inputs
        if element not in self.data["elements"].keys():
            raise KeyError(f"The element '{element}' in not defined in the config.")
        if operation_name not in self.data["elements"][element]["operations"].keys():
            raise KeyError(
                f"The operation '{operation_name}' in not defined in the config for the element '{element}'."
            )
        if (
            iw_op_name
            not in self.data["pulses"][self.data["elements"][element]["operations"][operation_name]][
                "integration_weights"
            ].keys()
        ):
            raise KeyError(
                f"The integration weight '{iw_op_name}' in not associated to the pulse corresponding to the operation '{operation_name}'."
            )
        # Update iw
        pulse_name = self.data["elements"][element]["operations"][operation_name]
        iw_name = self.data["pulses"][pulse_name]["integration_weights"][iw_op_name]
        count = 0
        for key in self.data["pulses"]:
            if "integration_weights" in self.data["pulses"][key]:
                if iw_name in self.data["pulses"][key]["integration_weights"].values():
                    count += 1
        if count > 1 and not force_update:
            raise Exception(
                "The updated integration weights are used in other operations. To force the update, please set the force_update flag to True."
            )
        elif count == 0:
            raise Exception(f"The integration weights {iw_op_name} are not listed in the config integration weights.")

        self.data["integration_weights"][iw_name] = {"cosine": iw_cos, "sine": iw_sin}

    def copy_operation(self, element: str, operation_name: str, new_name: str):
        """
        Copy an existing operation and rename it. This function is used to add similar operations that differ
        only from their waveforms than can be updated using the corresponding function `update_waveforms()`.

        :param element: name of the element to get the waveforms from. Must be defined in the config.
        :param operation_name: name of the operation to get the waveforms from. Must be defined in the config.
        :param new_name: name of the new operation.
        """
        # Check inputs
        if element not in self.data["elements"].keys():
            raise KeyError(f"The element '{element}' in not defined in the config.")
        if operation_name not in self.data["elements"][element]["operations"].keys():
            raise KeyError(
                f"The operation '{operation_name}' in not defined in the config for the element '{element}'."
            )
        # Copy operation
        pulse_name = self.data["elements"][element]["operations"][operation_name]
        self.data["pulses"][element + "_" + new_name + self.pulse_suffix] = _deepcopy(self.data["pulses"][pulse_name])
        # Rename the copied operation
        self.data["elements"][element]["operations"][new_name] = element + "_" + new_name + self.pulse_suffix

    def update_waveforms(
        self,
        element: str,
        operation_name: str,
        wf: Tuple[List[float], List[float]] or Tuple[List[float]],
    ):
        """
        Update the waveforms from a specific operation and element.

        :param element: name of the element to get the waveforms from. Must be defined in the config.
        :param operation_name: name of the operation to get the waveforms from. Must be defined in the config.
        :param wf: Tuple containing the updated waveforms. (wf_single,) for a singleInput element and (wf_i, wf_q) for a mixInputs element.
        """
        # Check inputs
        if element not in self.data["elements"].keys():
            raise KeyError(f"The element '{element}' in not defined in the config.")
        if operation_name not in self.data["elements"][element]["operations"].keys():
            raise KeyError(
                f"The operation '{operation_name}' in not defined in the config for the element '{element}'."
            )
        if "mixInputs" not in self.data["elements"][element].keys() and len(wf) == 2:
            raise KeyError(f"Element '{element}' is not a mixInputs element.")
        if "singleInput" not in self.data["elements"][element].keys() and len(wf) == 1:
            raise KeyError(f"Element '{element}' is not a singleInput element.")
        if len(wf) == 2:
            if len(wf[0]) != len(wf[1]):
                raise ValueError("The 'I' and 'Q' waveforms must have the same length.")

        pulse_name = self.data["elements"][element]["operations"][operation_name]
        self.data["pulses"][pulse_name]["length"] = len(wf[0])
        # mixInputs element
        if len(wf) == 2:
            wf_name = element + "_" + operation_name + self.wf_suffix
            wf_i = wf[0]
            wf_q = wf[1]
            if len(wf_i) > 0:
                if wf_i[:-1] == wf_i[1:]:
                    self.data["waveforms"][wf_name + "_i"] = {
                        "type": "constant",
                        "sample": wf_i[0],
                    }
                else:
                    self.data["waveforms"][wf_name + "_i"] = {
                        "type": "arbitrary",
                        "samples": list(wf_i),
                    }

                if wf_q[:-1] == wf_q[1:]:
                    self.data["waveforms"][wf_name + "_q"] = {
                        "type": "constant",
                        "sample": wf_q[0],
                    }
                else:
                    self.data["waveforms"][wf_name + "_q"] = {
                        "type": "arbitrary",
                        "samples": list(wf_q),
                    }

            else:
                raise ValueError("The waveforms must have at least one point.")
            self.data["pulses"][pulse_name]["waveforms"] = {
                "I": wf_name + "_i",
                "Q": wf_name + "_q",
            }

        elif len(wf) == 1:
            wf_name = element + "_" + operation_name + "_single" + self.wf_suffix
            wf_s = wf[0]
            if len(wf_s) > 0:
                if wf_s[:-1] == wf_s[1:]:
                    self.data["waveforms"][wf_name] = {
                        "type": "constant",
                        "sample": wf_s[0],
                    }
                else:
                    self.data["waveforms"][wf_name] = {
                        "type": "arbitrary",
                        "samples": list(wf_s),
                    }
            else:
                raise ValueError("The waveform must have at least one point.")

            self.data["pulses"][pulse_name]["waveforms"] = {
                "single": wf_name,
            }
