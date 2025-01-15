![PyPI](https://img.shields.io/pypi/v/qualang-tools)
[![discord](https://img.shields.io/discord/806244683403100171?label=QUA&logo=Discord&style=plastic)](https://discord.gg/7FfhhpswbP)

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

# QUA Language Tools

The QUA language tools package includes various tools useful while writing QUA programs and performing experiments.

It includes:


* [QUA Loops Tools](qualang_tools/loops/README.md) - This library includes tools for parametrizing QUA for_ loops using the numpy (linspace, arange, logspace) methods or by directly inputting a numpy array.
* [Plotting Tools](qualang_tools/plot/README.md) - This library includes tools to help handling plots from QUA programs.
* [Result Tools](qualang_tools/results/README.md) - This library includes tools for handling and fetching results from QUA programs, and saving them to the local file storage.
* [Units Tools](qualang_tools/units/README.md) - This library includes tools for using units (MHz, us, mV...) and converting data to other units (demodulated data to volts for instance).
* [Analysis Tools](qualang_tools/analysis/README.md) - This library includes tools for analyzing data from experiments. 
It currently has a two-states discriminator for analyzing the ground and excited IQ blobs.
* [Octave Tools](qualang_tools/octave_tools/README.md) - This library includes tools for controlling the Octave and extract/set the correction parameters from the calibration database.
* [Multi-user tools](qualang_tools/multi_user/README.md) - This library includes tools for working with the QOP in a multi-user or multi-process setting.
* [Simulator tools](qualang_tools/simulator/README.md) - This library includes tools for creating simulations.

* [Bakery](qualang_tools/bakery/README.md) - This library introduces a new framework for creating arbitrary waveforms and
storing them in the usual configuration file. It allows defining waveforms in a QUA-like manner while working with 1ns resolution (or higher).

* [External Frameworks](qualang_tools/external_frameworks/qcodes/README.md) - This library introduces drivers for integrating the OPX within external frameworks such as QCoDeS. Please refer to the [examples](./examples) section for more details about how to use these drivers.
* [Video Mode](qualang_tools/video_mode/README.md) - This module allows the user to update some pre-defined parameters of a QUA program while fetching data from the OPX for dynamic tuning. Please refer to the [examples](./examples/video_mode) section for more details about how to implement this module.

* Addons:
  * [Calibrations](qualang_tools/addons/calibration/README.md) - This module allows to easily perform most of the standard single qubit calibrations from a single python file.
  * [Interactive Plot Library](qualang_tools/addons/README.md) - This package drastically extends the capabilities of matplotlib,
  enables easily editing various parts of the figure, copy-pasting data between figures and into spreadsheets, 
  fitting the data and saving the figures.
  * [assign_variables_to_element](qualang_tools/addons/variables.py) - Forces the given variables to be used by the given element thread. Useful as a workaround for when the compiler
  wrongly assigns variables which can cause gaps.

* [Config Tools](qualang_tools/config/README.md) - This package includes tools related to the QOP configuration file, including:
  * [Integration Weights Tools](qualang_tools/config/README_integration_weights_tools.md) - This package includes tools for the creation and manipulation of integration weights. 
  * [Waveform Tools](qualang_tools/config/README_waveform_tools.md) - This package includes tools for creating waveforms useful for experiments with the QOP.
  * [Config Helper Tools](qualang_tools/config/README_helper_tools.md) - This package includes tools for writing and updating the configuration.
  * [Config GUI](qualang_tools/config/README_config_GUI.md) - This package contains a GUI for creating and visualizing the configuration file - No longer being actively developed.
  * [Config Builder](qualang_tools/config/README_config_builder.md) - This package contains an API for creating and manipulation configuration files - No longer being actively developed.

* [Control Panel](qualang_tools/control_panel/README.md)- This package includes tools for directly controlling the OPX.
  * [ManualOutputControl](qualang_tools/control_panel/README_manual_output_control.md) - This module allows controlling the outputs from the OPX in CW mode. Once created, it has an API for defining which channels are on. Analog channels also have an API for defining their amplitude and frequency.
  * [VNA](qualang_tools/control_panel/README_vna.md) - This module allows to configure the OPX as a VNA for a given element (readout resonator for instance) and operation (readout pulse for instance) already defined in the configuration. Once created, it has an API for defining which measurements are to be run depending on the down-conversion solution used (ED: envelope detector, IR: image rejection mixer, IQ: IQ mixer).
* [Macros](qualang_tools/macros/README.md) - This module includes convenience functions for encapsulating common QUA code.
* [Digital filters](qualang_tools/digital_filters/README.md) - Library of functions allowing the derivation of the digital filter taps to correct distortions.

* [Voltage Gates](qualang_tools/voltage_gates/README.md) - The `VoltageGateSequence` class facilitates the creation and management of complex pulse sequences for quantum operations, allowing for dynamic voltage control, ramping, and bias compensation across multiple gate elements.
* [Wirer](qualang_tools/wirer/README.md) - The `wirer` tool allows for automatic allocation of arbitrary channels to an arbitrary combination of instruments.

## Installation

Install the current version using `pip`, the `--upgrade` flag ensures that you will get the latest version.

```bash
pip install --upgrade qualang-tools
```

Note that in order use the `Config GUI` or `Config Builder`, you need to install using
```bash
pip install --upgrade qualang-tools[configbuilder]
```

Note that in order use the `Interactive Plot Library`, you need to install using
```bash
pip install --upgrade qualang-tools[interplot]
```

## Support and Contribution
Have an idea for another tool? A way to improve an existing one? Found a bug in our code?

We'll be happy if you could let us know by opening an [issue](https://github.com/qua-platform/py-qua-tools/issues) on the [GitHub repository](https://github.com/qua-platform/py-qua-tools).

Feel like contributing code to this library? We're thrilled! Please follow [this guide](https://github.com/qua-platform/py-qua-tools/blob/main/CONTRIBUTING.md) and feel free to contact us if you need any help, you can do it by opening an [issue](https://github.com/qua-platform/py-qua-tools/issues) :)

## Usage

Examples for using various tools can be found on the [QUA Libraries Repository](https://github.com/qua-platform/qua-libs).

Examples for using the Baking toolbox, including 1-qubit randomized benchmarking, cross-entropy benchmark (XEB), high sampling rate baking and more can be found [here](https://github.com/qua-platform/qua-libs/tree/main/examples/bakery).
