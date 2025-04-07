from qm.results.simulator_samples import SimulatorControllerSamples

from .helpers import copy_nested_dict, iterate_nested_dict, update_nested_dict
from .data_processor import DataProcessor


class SimulatorControllerSamplesSaver(DataProcessor):
    def process(self, data):
        processed_data = copy_nested_dict(data)
        for keys, val in iterate_nested_dict(data):
            if not isinstance(val, SimulatorControllerSamples):
                continue

            update_nested_dict(processed_data, keys, None)

        return processed_data
