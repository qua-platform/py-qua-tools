# QUA Language Tools

The QUA language tools package includes various tools useful while writing QUA programs and performing experiments.

It includes:

- The baking tool which allows defining waveforms in a QUA-like manner with for working with a 1ns resolution.  It can also be used to create even higher resolution waveforms.
- Tools for converting a list of integration weights into the format used in the configuration.
- Tools for creating waveforms commonly used in Quantum Science.
- Tools for correcting mixer imbalances.

## Support and Contribution
Have an idea for another tool? A way to improve an existing one? Found a bug in our code?

We'll be happy if you could let us know by opening an [issue](https://github.com/qua-platform/py-qua-tools/issues) on the [GitHub repository](https://github.com/qua-platform/py-qua-tools).

Feel like contributing code to this library? We're thrilled! Please follow [this guide](https://github.com/qua-platform/py-qua-tools/blob/main/CONTRIBUTING.md) and feel free to contact us if you need any help, you can do it by opening an [issue](https://github.com/qua-platform/py-qua-tools/issues) :)

## Installation

Install the current version using `pip`, the `--upgrade` flag ensures that you will get the latest version.

```
pip install --upgrade qualang-tools
```

## Usage

Examples for using various tools can be found on the [QUA Libraries Repository](https://github.com/qua-platform/qua-libs).

Examples for using the Baking toolbox, including 1-qubit randomized benchmarking, cross-entropy benchmark (XEB), high sampling rate baking and more can be found [here](https://github.com/qua-platform/qua-libs/tree/main/examples/bakery).
