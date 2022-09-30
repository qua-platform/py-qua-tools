from collections import UserDict as _UserDict
from copy import deepcopy as _deepcopy
from typing import List
from numpy import np
import json as _json


class QuaConfig(_UserDict):
    def __init__(self, data):
        super().__init__(data)
        self._data_orig = _deepcopy(data)

    def add_control_operation_iq(self, element, operation_name, wf_i, wf_q):
        pulse_name = element + "_" + operation_name + "_in"
        self.data["waveforms"][pulse_name + "_i"] = {
            "type": "arbitrary",
            "samples": list(wf_i),
        }
        self.data["waveforms"][pulse_name + "_q"] = {
            "type": "arbitrary",
            "samples": list(wf_q),
        }
        self.data["pulses"][pulse_name] = {
            "operation": "control",
            "length": len(wf_i),
            "waveforms": {"I": pulse_name + "_i", "Q": pulse_name + "_q"},
        }
        self.data["elements"][element]["operations"][operation_name] = pulse_name

    def add_control_operation_single(self, element, operation_name, wf):
        pulse_name = element + "_" + operation_name + "_in"
        self.data["waveforms"][pulse_name + "_single"] = {
            "type": "arbitrary",
            "samples": list(wf),
        }
        self.data["pulses"][pulse_name] = {
            "operation": "control",
            "length": len(wf),
            "waveforms": {"single": pulse_name + "_single"},
        }
        self.data["elements"][element]["operations"][operation_name] = pulse_name

    def copy_measurement_operation(self, element, operation_name, new_name):
        pulse_name = self.data["elements"][element]["operations"][operation_name]
        self.data["pulses"][new_name + "in"] = _deepcopy(
            self.data["pulses"][pulse_name]
        )
        self.data["elements"][element]["operations"][new_name] = new_name + "in"

    def update_measurement_waveforms(self, element, operation_name, wf_i, wf_q):
        pulse_name = self.data["elements"][element]["operations"][operation_name]
        self.data["waveforms"][pulse_name + "_i"] = {
            "type": "arbitrary",
            "samples": list(wf_i),
        }
        self.data["waveforms"][pulse_name + "_q"] = {
            "type": "arbitrary",
            "samples": list(wf_q),
        }
        self.data["pulses"][pulse_name]["waveforms"] = {
            "I": pulse_name + "_i",
            "Q": pulse_name + "_q",
        }
        self.data["pulses"][pulse_name]["length"] = len(wf_i)

    def update_measurement_iws(
        self, element, operation_name, iw_op_name, iw_cos, iw_sin
    ):
        pulse_name = self.data["elements"][element]["operations"][operation_name]
        iw_name = self.data["pulses"][pulse_name]["integration_weights"][iw_op_name]
        self.data["integration_weights"][iw_name] = {"cosine": iw_cos, "sine": iw_sin}

    def reset(self):
        self.data = _deepcopy(self._data_orig)

    def dump(self, filename):
        with open(filename, "w") as fp:
            _json.dump(self.data, fp)

    def get_waveforms_from_op(self, element, operation):
        pulse = self.get_pulse_from_op(element, operation)
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

    def get_pulse_from_op(self, element, operation):
        return self.data["pulses"][
            self.data["elements"][element]["operations"][operation]
        ]

    def update_op_amp(self, element, operation, amp):
        pulse = self.get_pulse_from_op(element, operation)
        try:
            self.data["waveforms"][pulse["waveforms"]["single"]]["sample"] = amp
        except KeyError:
            raise KeyError(
                "Can only access amplitude for a constant pulse of a single element"
            )

    def get_op_amp(self, element, operation):
        pulse = self.get_pulse_from_op(element, operation)
        try:
            return self.data["waveforms"][pulse["waveforms"]["single"]]["sample"]
        except KeyError:
            raise KeyError(
                "Can only access amplitude for a constant pulse of a single element"
            )


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
    config = QuaConfig(config)
    for q in qubits:
        xy = resolve(q, "xy")
        x_i, x_q = config.get_waveforms_from_op(xy, "x")

        base_pulse_180 = x_i, x_q
        half_pi_amp = params.half_pi_amp[q]
        pi_amp = params.pi_amp[q]
        base_pulse_90 = half_pi_amp / pi_amp * np.array([x_i, x_q])
        config.add_control_operation_iq(xy, "y", base_pulse_180[1], base_pulse_180[0])
        config.add_control_operation_iq(xy, "sy", base_pulse_90[1], base_pulse_90[0])
        config.add_control_operation_iq(xy, "-sy", -base_pulse_90[1], -base_pulse_90[0])
        config.add_control_operation_iq(xy, "sx", base_pulse_90[0], base_pulse_90[1])
        config.add_control_operation_iq(xy, "-sx", -base_pulse_90[0], -base_pulse_90[1])
    return config.data
