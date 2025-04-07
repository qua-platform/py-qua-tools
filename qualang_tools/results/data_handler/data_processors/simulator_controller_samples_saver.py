import logging

from qm.results.simulator_samples import SimulatorControllerSamples

from .helpers import copy_nested_dict, iterate_nested_dict, update_nested_dict
from .data_processor import DataProcessor


logger = logging.getLogger(__name__)


class SimulatorControllerSamplesSaver(DataProcessor):
    def process(self, data):
        processed_data = copy_nested_dict(data)
        for keys, val in iterate_nested_dict(d=data):
            if not isinstance(val, SimulatorControllerSamples):
                continue

            try:
                serialised_samples = {
                    # analog structure: {"{int}-{int}: array}
                    "analog": dict(val.analog),
                    "digital": dict(val.digital),
                    "analog_sampling_rate": dict(getattr(val, "analog_sampling_rate", None)),
                }
            except Exception:
                logger.warning(f"Could not serialise simulator controller samples for {keys}")
                continue

            update_nested_dict(processed_data, keys, serialised_samples)

        return processed_data
