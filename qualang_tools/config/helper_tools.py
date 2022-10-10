from collections import UserDict as _UserDict
from copy import deepcopy as _deepcopy
from typing import List, Tuple
import numpy as np
import json as _json
from pprint import pprint


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

    def add_control_operation_iq(
        self, element: str, operation_name: str, wf_i: List[float], wf_q: List[float]
    ):
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
        if len(wf_i) > 0:
            if wf_i[:-1] == wf_i[1:]:
                self.data["waveforms"][wf_name + "_i"] = {
                    "type": "constant",
                    "sample": wf_i[0],
                }
                self.data["waveforms"][wf_name + "_q"] = {
                    "type": "constant",
                    "sample": wf_q[0],
                }
            else:
                self.data["waveforms"][wf_name + "_i"] = {
                    "type": "arbitrary",
                    "samples": list(wf_i),
                }
                self.data["waveforms"][wf_name + "_q"] = {
                    "type": "arbitrary",
                    "samples": list(wf_q),
                }
        elif len(wf_i) == 1:
            self.data["waveforms"][wf_name + "_i"] = {
                "type": "constant",
                "sample": wf_i[0],
            }
            self.data["waveforms"][wf_name + "_q"] = {
                "type": "constant",
                "sample": wf_q[0],
            }
        else:
            raise ValueError("The waveforms must have at least one point.")

    def add_control_operation_single(
        self, element: str, operation_name: str, wf: List[float]
    ):
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
        if len(wf) > 1:
            if wf[:-1] == wf[1:]:
                self.data["waveforms"][wf_name] = {
                    "type": "constant",
                    "sample": wf[0],
                }
            else:
                self.data["waveforms"][wf_name] = {
                    "type": "arbitrary",
                    "samples": list(wf),
                }
        elif len(wf) == 1:
            self.data["waveforms"][wf_name] = {
                "type": "constant",
                "sample": wf[0],
            }
        else:
            raise ValueError("The waveform must have at least one point.")

    def get_waveforms_from_op(
        self, element: str, operation_name: str
    ) -> List or List[List]:
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

        return self.data["pulses"][
            self.data["elements"][element]["operations"][operation_name]
        ]

    def update_op_amp(self, element: str, operation_name: str, amp: float):
        """
        Update the operation amplitude.
        Can only access amplitude for a constant pulse of a single element.

        :param element: name of the element to get the waveforms from. Must be defined in the config.
        :param operation_name: name of the operation to get the waveforms from. Must be defined in the config.
        :param amp: float for the updated amplitude. Must be within the range [-0.5, 0.5) V.
        """

        # Check inputs
        if element not in self.data["elements"].keys():
            raise KeyError(f"The element '{element}' in not defined in the config.")
        if operation_name not in self.data["elements"][element]["operations"].keys():
            raise KeyError(
                f"The operation '{operation_name}' in not defined in the config for the element '{element}'."
            )
        if not -0.5 <= amp < 0.5:
            raise ValueError(
                "The amplitude must be within the range [-0.5, 0.5) Volts."
            )

        pulse = self.get_pulse_from_op(element, operation_name)
        try:
            self.data["waveforms"][pulse["waveforms"]["single"]]["sample"] = amp
        except KeyError:
            raise KeyError(
                "Can only access amplitude for a constant pulse of a single element"
            )

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
            raise KeyError(
                "Can only access amplitude for a constant pulse of a single element"
            )

    def update_integration_weight(
        self,
        element: str,
        operation_name: str,
        iw_op_name: str,
        iw_cos: List,
        iw_sin: List,
    ):
        """
        Update the cosine and sine parts of an integration weight for a given element and operation.

        :param element: name of the element to get the waveforms from. Must be defined in the config.
        :param operation_name: name of the operation to get the waveforms from. Must be defined in the config.
        :param iw_op_name: name of the integration weight to be updated. Must be defined in the config.
        :param iw_cos: values for the cosine part of integration weights defined as a list of tuples [(value, duration in ns)].
        :param iw_sin: values for the sine part of integration weights defined as a list of tuples [(value, duration in ns)].
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
            not in self.data["pulses"][
                self.data["elements"][element]["operations"][operation_name]
            ]["integration_weights"].keys()
        ):
            raise KeyError(
                f"The integration weight '{iw_op_name}' in not associated to the pulse corresponding to the operation '{operation_name}'."
            )
        # Update iw
        pulse_name = self.data["elements"][element]["operations"][operation_name]
        iw_name = self.data["pulses"][pulse_name]["integration_weights"][iw_op_name]
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
        self.data["pulses"][element + "_" + new_name + self.pulse_suffix] = _deepcopy(
            self.data["pulses"][pulse_name]
        )
        # Rename the copied operation
        self.data["elements"][element]["operations"][new_name] = (
            element + "_" + new_name + self.pulse_suffix
        )

    def update_waveforms(
        self,
        element: str,
        operation_name: str,
        wf: Tuple[List[float], List[float]] or Tuple[List[float]],
    ):
        """

        :param element: name of the element to get the waveforms from. Must be defined in the config.
        :param operation_name: name of the operation to get the waveforms from. Must be defined in the config.
        :param wf:
        :return:
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
            self.data["waveforms"][wf_name + "_i"] = {
                "type": "arbitrary",
                "samples": list(wf_i),
            }
            self.data["waveforms"][wf_name + "_q"] = {
                "type": "arbitrary",
                "samples": list(wf_q),
            }
            self.data["pulses"][pulse_name]["waveforms"] = {
                "I": wf_name + "_i",
                "Q": wf_name + "_q",
            }
        elif len(wf) == 1:
            wf_name = element + "_" + operation_name + "_single" + self.wf_suffix
            wf_s = wf[0]
            self.data["waveforms"][wf_name] = {
                "type": "arbitrary",
                "samples": list(wf_s),
            }
            self.data["pulses"][pulse_name]["waveforms"] = {
                "single": wf_name,
            }


def resolve(qubit: int, channel: str):
    if channel == "xy":
        element = f"qb{qubit}"
    elif channel == "z":
        element = f"qb{qubit}_flux_line"
    elif channel == "rr":
        element = f"qb{qubit}_rr"
    else:
        raise ValueError(f"unknown channel {channel} for qubit {qubit}")
    return element


def add_90_degree_rotation_pulses(config: dict, qubits: List[int], params) -> dict:
    config = QuaConfig(config)  # TODO: params is from entropy right?
    for q in qubits:
        xy = resolve(
            q, "xy"
        )  # TODO: do we really need this? can't we just input the list of elements?
        x_i, x_q = config.get_waveforms_from_op(xy, "x")

        base_pulse_180 = x_i, x_q
        half_pi_amp = params.half_pi_amp[q]
        pi_amp = params.pi_amp[q]
        base_pulse_90 = half_pi_amp / pi_amp * np.array([x_i, x_q])
        config.add_control_operation_iq(xy, "y", base_pulse_180[1], base_pulse_180[0])
        config.add_control_operation_iq(
            xy, "sy", base_pulse_90[1], base_pulse_90[0]
        )  # TODO: is sy an official name for y90?
        config.add_control_operation_iq(xy, "-sy", -base_pulse_90[1], -base_pulse_90[0])
        config.add_control_operation_iq(xy, "sx", base_pulse_90[0], base_pulse_90[1])
        config.add_control_operation_iq(xy, "-sx", -base_pulse_90[0], -base_pulse_90[1])
    return config.data
