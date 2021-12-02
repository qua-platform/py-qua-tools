# qualang_tools

The qualang_tools package includes tools for facilitating writing of QUA programs and configurations in Python. 

It includes:

- The baking tool which allows defining waveforms in a QUA-like manner with for working with a 1ns resolution.  It can also be used to create even higher resolution waveforms.
- Tools for converting a list of integration weights into the format used in the configuration.
- Tools for creating waveforms commonly used in Quantum Science.
- Tools for correcting mixer imbalances.

## Installation

Install the current version using `pip`, the `--upgrade` flag ensures that you will get the latest version 

```
pip install --upgrade qualang-tools
```

## Usage

Examples for 1-qubit randomized benchmarking, cross-entropy benchmark (XEB), high sampling rate baking and more  can be found in the examples folder of the [py-qua-tools repository](https://github.com/qua-platform/py-qua-tools/)


