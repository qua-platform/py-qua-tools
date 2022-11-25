# Helper Tools

## Introduction
This package includes tools for writing and updating the configuration. 

## Functions
All the tools are implemented as methods in a Python class called QuaConfig.
The available functions are:
* `add_control_operation_single` - Add or update a control operation to a mixed input element.
* `add_control_operation_iq` - Add or update a control operation to a single input element.
* `get_waveforms_from_op` - Get the waveforms corresponding to the given element and operation.
* `get_pulse_from_op` - Get the pulse corresponding to the given element and operation.
* `get_op_amp` - Get the operation amplitude.
* `update_op_amp` - Update the operation amplitude.
* `update_integration_weight` - Update the cosine and sine parts of an integration weight for a given element and operation.
* `copy_operation` - Copy an existing operation and rename it. This function is used to add similar operations that differ
        only from their waveforms than can be updated using the corresponding function `update_waveforms()`.
* `update_waveforms` - Update the waveforms from a specific operation and element.

## Example use case
Usage example of the helper tools:

```python
from qualang_tools.config.helper_tools import QuaConfig
from configuration import config
from scipy.signal.windows import gaussian

# Initialize the QuaConfig class
conf = QuaConfig(config)

# Add control operations
## with arbitrary waveforms
config.add_control_operation_iq("qubit", "gate", (0.25*gaussian(136, 30)).tolist(), [0.0]*136)
## with constant waveforms
config.add_control_operation_iq("resonator", "long_readout", [0.1 for _ in range(112)], [0.0 for _ in range(112)])
## with singleInput elements
config.add_control_operation_single("flux_line", "bias", [0.1 for _ in range(112)])

# Update integration weights
config.update_integration_weight("resonator", "readout", "cos", [(1, 80)], [(0, 80)])
config.update_integration_weight("resonator", "readout", "sin", [(0, 80)], [(1, 80)])
config.update_integration_weight("resonator", "readout", "minus_sin", [(0, 80)], [(-1, 80)])

# Get an operation waveform
## for a mixInputs element
previous_bias_wf = config.get_waveforms_from_op("flux_line", "bias")
## For a singleInput element
readout_wf_i, readout_wf_q = config.get_waveforms_from_op("resonator", "readout")

# Update an operation amplitude (only for constant waveforms)
config.update_op_amp("flux_line", "bias", 0.05)

# Add a measurement operation from an existing operation
config.copy_operation("resonator", "readout", new_name="short_readout")

# Update an operation waveform
## with mixInputs elements & arbitrary waveforms
config.update_waveforms("resonator", "short_readout", ((0.15*gaussian(175, 30)).tolist(), [0.0]*175))
## with singleInput elements & constant waveform
config.update_waveforms("flux_line", "bias", ([0.118]*175, ))
```
