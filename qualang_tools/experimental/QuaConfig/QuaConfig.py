from collections import UserDict as _UserDict
from copy import deepcopy as _deepcopy
import json as _json
from typing import Union, Tuple, List


class QuaConfig(_UserDict):

    def __init__(self, data: dict):
        """

        :param data:
        """
        super().__init__(data)
        self._data_orig = _deepcopy(data)


    def add_control_operation_iq(self, *, element, operation_name, wf_i, wf_q):
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
            self, element: str, operation_name: str, iw_op_name: str, iw_cos, iw_sin
    ):
        """
        update the integration weights associated with a specific operation
        :param element:
        :param operation_name:
        :param iw_op_name:
        :param iw_cos:
        :param iw_sin:
        :return:
        """
        # self.elements[element].operations[operation_name].integration_weights[iw_op_name].update(cosine=iw_cos,sine=iw_sin)

        pulse_name = self.data["elements"][element]["operations"][operation_name]
        iw_name = self.data["pulses"][pulse_name]["integration_weights"][iw_op_name]
        self.data["integration_weights"][iw_name] = {"cosine": iw_cos, "sine": iw_sin}

    def reset(self):
        """
        revert the QuaConfig to its original state (set by _data_)
        :return:
        """
        self.data = _deepcopy(self._data_orig)

    def dump(self, filename: str):
        """

        :param filename:
        :return:
        """
        with open("config.json", "w") as fp:
            _json.dump(self.data, fp)

    def get_waveforms_from_op(
            self, element: str, operation: str
    ) -> Union[Tuple[List[float], List[float]], List[float]]:
        """
        Get output waveforms associated with an operation on a quantum element.
        For both arbitrary and constant pulses, the waveform returned will be the actual values played.
        :param element: Name of the element
        :param operation: Name of the operation
        :return: Either a waveform entries list if element is of type singleInput, or a tuple of waveform entries list if element is of type mixedInputs.
        """
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

    def update_intermediate_frequency(
            self, element: str, new_if: float, strict=True
    ) -> None:
        """
        Update an intermediate frequency for an element,
        either updating the entry in the mixer's calibration matrix list or not depending on strict flag
        :param element: the name of the element
        :param new_if: frequency to change to
        :param strict: if `True`, will not update correction matrix. If false, will also replace the entry
        in the corresponding correction matrix
        """
        old_if = self.data["elements"][element]["intermediate_frequency"]
        if not strict:
            self.data["elements"][element]["intermediate_frequency"] = new_if
            mixer = self.data["elements"][element]["mixInputs"]["mixer"]
            lo_freq = self.data["elements"][element]["mixInputs"]["lo_frequency"]
            found_entry_index = None
            for entry in self.data["mixers"][mixer]:
                if (
                        entry["intermediate_frequency"] == old_if
                        and entry["lo_frequency"] == lo_freq
                ):
                    found_entry_index = entry
            self.data["mixers"][mixer][found_entry_index][
                "intermediate_frequency"
            ] = new_if

    def update_op_amp(self, element: str, operation: str, amp: float):
        """

        :param element:
        :param operation:
        :param amp:
        :return:
        """
        pulse = self.get_pulse_from_op(element, operation)
        if "sample" not in self.data["waveforms"][pulse["waveforms"]["single"]]:
            raise KeyError(
                "Can only access amplitude for a constant pulse of a single element"
            )
        else:
            self.data["waveforms"][pulse["waveforms"]["single"]]["sample"] = amp

    def get_op_amp(self, element, operation):
        """
        DEPRECATED - DO NOT USE
        use `get_waveforms_from_op` instead
        """
        pulse = self.get_pulse_from_op(element, operation)
        try:
            return self.data["waveforms"][pulse["waveforms"]["single"]]["sample"]
        except KeyError:
            raise KeyError(
                "Can only access amplitude for a constant pulse of a single element"
            )

    def get_port_by_element_input(
            self, element: str, element_input: str
    ) -> Tuple[str, int]:
        """
        returns the ports of a quantum element.
        :param element: Name of the element
        :param element_input:
            Name of the element port. Can be either 'single' if element has `singleInput`
            or 'I', 'Q' if element has mixed inputs.
        :return: a tuple of the form (con_name, port number)
        """
        element_data = self.data["elements"][element]
        if element_input == "single":
            if "singleInput" in element_data:
                return element_data["singleInput"]["port"]
            else:
                raise ValueError(
                    "can only use 'single' for a singleInput quantum element"
                )
        if "mixInputs" in element_data:
            if element_input == "I" or element_input == "Q":
                return element_data["mixInputs"][element_input]
            else:
                raise ValueError(
                    "can only use 'I' or 'Q' for a mixInputs quantum element"
                )
        else:
            raise ValueError(
                f"element input is {element_input} but can only be I, Q for mixInputs or "
                f"single for singleInput"
            )

    def set_output_dc_offset_by_element(
            self, element: str, port: str, offset: float
    ) -> None:
        """
        Set a DC offset value by element
        :param element: Name of the element
        :param port: Name of the port. Can be either 'single' if element has `singleInput` or 'I', 'Q' if element has mixed inputs.
        :param offset: offset value to set
        """
        con, port = self.get_port_by_element_input(element, port)
        if port in self.data["controllers"][con]["analog_outputs"]:
            self.data["controllers"][con]["analog_outputs"][port]["offset"] = offset
        else:
            self.data["controllers"][con]["analog_outputs"][port] = {"offset": offset}
