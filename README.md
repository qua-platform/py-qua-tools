![PyPI](https://img.shields.io/pypi/v/qualang-tools)
[![discord](https://img.shields.io/discord/806244683403100171?label=QUA&logo=Discord&style=plastic)](https://discord.gg/7FfhhpswbP)

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

# QUA Language Tools

The QUA language tools package includes various tools useful while writing QUA programs and performing experiments.

It includes:

* [Bakery](qualang_tools/bakery/README.md) - This library introduces a new framework for creating arbitrary waveforms and
storing them in the usual configuration file. It allows defining waveforms in a QUA-like manner while working with 1ns resolution (or higher).

* [Interactive Plot Library](qualang_tools/addons/README.md) - This package drastically extends the capabilities of matplotlib,
enables easily editing various parts of the figure, copy-pasting data between figures and into spreadsheets, 
fitting the data and saving the figures.

* [Config Tools](qualang_tools/config/README.md) - This package includes tools related to the QOP configuration file, including:
  * [Integration Weights Tools](README_integration_weights_tools.md) - This package includes tools for the creation and manipulation of integration weights. 
  * [Waveform Tools](README_waveform_tools.md) - This package includes tools for creating waveforms useful for experiments with the QOP.
  * [Config GUI](README_config_GUI.md) - This package contains a GUI for creating and visualizing the configuration file.
  * [Config Builder](README_config_builder.md) - This package contains an API for creating and manipulation configuration files.

* [Control Panel](qualang_tools/control_panel/README.md)- This package includes tools for directly controlling the OPX.
  * [ManualOutputControl](README_manual_output_control.md) - This module allows controlling the outputs from the OPX in CW mode. Once created, it has an API for defining which channels are on. Analog channels also have an API for defining their amplitude and frequency.
  * [VNA](README_vna.md) - This module allows to configure the OPX as a VNA for a given element (readout resonator for instance) and operation (readout pulse for instance) already defined in the configuration. Once created, it has an API for defining which measurements are to be run depending on the down-conversion solution used (ED: envelope detector, IR: image rejection mixer, IQ: IQ mixer).

## Installation

Install the current version using `pip`, the `--upgrade` flag ensures that you will get the latest version.

```commandline
pip install --upgrade qualang-tools
```

## Support and Contribution
Have an idea for another tool? A way to improve an existing one? Found a bug in our code?

We'll be happy if you could let us know by opening an [issue](https://github.com/qua-platform/py-qua-tools/issues) on the [GitHub repository](https://github.com/qua-platform/py-qua-tools).

Feel like contributing code to this library? We're thrilled! Please follow [this guide](https://github.com/qua-platform/py-qua-tools/blob/main/CONTRIBUTING.md) and feel free to contact us if you need any help, you can do it by opening an [issue](https://github.com/qua-platform/py-qua-tools/issues) :)

## Usage

Examples for using various tools can be found on the [QUA Libraries Repository](https://github.com/qua-platform/qua-libs).

Examples for using the Baking toolbox, including 1-qubit randomized benchmarking, cross-entropy benchmark (XEB), high sampling rate baking and more can be found [here](https://github.com/qua-platform/qua-libs/tree/main/examples/bakery).
